from utc.src.semestral.evolutionary import Individual
from utc.src.semestral.tl_constants import WINDOW, MIN_GREEN_TIME, YELLOW_DURATION
from utc.src.utils.xml_object import XmlObject, Element
import traci
import numpy as np
from typing import List
from copy import deepcopy


class TrafficLights(XmlObject):
    """
    Class representing single TrafficLights in simulation
    """
    def __init__(self, id: str, phases: List[traci.trafficlight.Phase]):
        """
        :param id: identifier of traffic lights (same as road network Junction)
        :param phases: original green phases of traffic lights extracted from road network
        """
        # Set programID as 1, so that it replaces the original in the road network (which is 0)
        super().__init__("tlLogic", {"id": id, "programID": 1, "offset": 0, "type": "static"})
        self.green_phases: List[traci.trafficlight.Phase] = [
            phase for phase in phases if ("G" in phase.state or "g" in phase.state)
        ]
        self.yellow_phases: List[traci.trafficlight.Phase] = [phase for phase in phases if "y" in phase.state]
        # History of TrafficLight phases during simulation (the one which were used to simulate further)
        self.history: List[List[traci.trafficlight.Phase]] = []
        # Checks
        assert (traci.isLoaded())
        assert(len(self.green_phases) == len(self.yellow_phases))
        assert(all(
            self.green_phases[i].state.replace("G", "y").replace("g", "y") ==
            self.yellow_phases[i].state for i in range(len(self.green_phases))
        ))
        assert(self.get_attribute("id") in traci.trafficlight.getIDList())
        self.total_phases: int = len(self.green_phases)
        self.next_phase: int = 0

    def update_tl(self, individual: Individual) -> None:
        """
        Updates the current tl program phases durations to given times,
        if the length of times is longer than total green phases, multiple
        cycles will be defined as such. Also checks for current phase and its
        remaining time.

        :param individual: individual containing green times
        :return: None
        """
        # print(f"Updating traffic lights: {self.id}, with timer: {individual.value}")
        assert ((np.sum(individual.value) + YELLOW_DURATION * individual.value.size) >= WINDOW)
        assert (traci.isLoaded())
        # Get the phase of traffic lights (we always optimize current state), since simulation state
        # is saved with the traffic lights set to the next phase already
        index: int = self.next_phase
        # Generate appropriate phases (there can be multiple same ones, since WINDOW may be higher than
        # the number of phases this TL have), or it can be lower
        accumulated: float = 0
        phases: List[traci.trafficlight.Phase] = []
        for timer in individual.value:
            # Surpassed timer, increase previous green timer\s
            if accumulated + timer + YELLOW_DURATION > WINDOW:
                missing: float = np.round(WINDOW - accumulated, decimals=2)
                # Unable to decrease current timer, increase yellow phases
                if missing < (MIN_GREEN_TIME + YELLOW_DURATION):
                    accumulated += missing
                    missing = np.round(missing / (len(phases) / 2), decimals=2)
                    for j in range(1, len(phases), 2):
                        phases[j].duration += missing
                    # Solve minor imprecision when working with double digits precision
                    if sum(phase.duration for phase in phases) > WINDOW:
                        phases[-1].duration -= np.round(WINDOW - sum(phase.duration for phase in phases), 2)
                    elif sum(phase.duration for phase in phases) < WINDOW:
                        phases[-1].duration += np.round(WINDOW - sum(phase.duration for phase in phases), 2)
                    break
                else:  # Fix current timer
                    timer = np.round(missing - YELLOW_DURATION, decimals=2)
            # Add phases, update timer
            phases.append(traci.trafficlight.Phase(np.round(timer, 2), self.green_phases[index].state))
            phases.append(traci.trafficlight.Phase(YELLOW_DURATION, self.yellow_phases[index].state))
            accumulated = np.round(accumulated + timer + YELLOW_DURATION, decimals=2)
            if WINDOW - 0.1 <= accumulated <= WINDOW + 0.1:
                break
            # Generate next green phase from cycle
            index = (index + 1) % self.total_phases
        # Account and solve minor time difference (rounding errors)
        assert(WINDOW - 0.1 <= np.round(sum(phase.duration for phase in phases), decimals=2) <= WINDOW + 0.1)
        if np.round(sum(phase.duration for phase in phases), decimals=2) < WINDOW:
            phases[-1].duration += np.round(WINDOW - sum(phase.duration for phase in phases), decimals=2)
        assert(WINDOW <= np.round(sum(phase.duration for phase in phases), decimals=2) <= WINDOW + 0.1)
        # Assign new logic program to TL (With id 1)
        traci.trafficlight.setProgramLogic(
            self.get_attribute("id"), traci.trafficlight.Logic(1, 0, 0, phases=tuple(phases))
        )
        traci.trafficlight.setProgram(self.get_attribute("id"), 1)
        return

    # ----------------------------------------- Utils -----------------------------------------

    def save_state(self) -> None:
        """
        Saves the current states of traffic lights insides 'history' list,
        calculates next phase

        :return: None
        """
        assert (traci.isLoaded())
        self.history.append(deepcopy(list(traci.trafficlight.getAllProgramLogics(self.get_attribute("id"))[1].phases)))
        # We guarantee ending at yellow phase and last index of program
        state: str = traci.trafficlight.getRedYellowGreenState(self.get_attribute("id"))
        assert(state == self.history[-1][-1].state)
        assert(traci.trafficlight.getProgram(self.get_attribute('id')) == "1")
        assert(state == traci.trafficlight.getAllProgramLogics(self.get_attribute('id'))[1].phases[-1].state)
        # Find the next phase
        for i, phase in enumerate(self.yellow_phases):
            if phase.state == state:
                self.next_phase = (i + 1) % self.total_phases
                break

    def check_phases(self, phases: List[Element]) -> bool:
        """
        :param phases:
        :return:
        """
        # print(f"Checking phases for tl: {self.get_attribute('id')}, total phases: {self.total_phases}")
        expected: str = self.green_phases[0].state
        green: bool = True
        index: int = 0
        for i, phase in enumerate(phases):
            if phase.tag != "phase":
                print(f"Invalid elements, expected phase, got: {phase.tag, phase.attrib}")
                return False
            # print(f"Index: {index}, i: {i}, expected: {expected}, green: {green}, state: {phase.attrib['state']}")
            if green and phase.attrib["state"] != self.green_phases[index].state:
                print(
                    f"Invalid green state at index: {i}, "
                    f"got: {phase.attrib['state']}, expected: {self.green_phases[index].state}"
                )
                return False
            elif not green and phase.attrib["state"] != self.yellow_phases[index].state:
                print(
                    f"Invalid yellow state at index: {i}, "
                    f"got: {phase.attrib['state']}, expected: {self.green_phases[index].state}"
                )
                return False
            elif phase.attrib["state"] != expected:
                print(f"Error, expected state: {expected}, got: {phase.attrib['state']} at index: {i}")
                return False
            index = (index if green else (index+1) % self.total_phases)
            # Next phase
            expected = (
                self.yellow_phases[index].state if green
                # Switch from yellow to next green
                else self.green_phases[index].state
            )
            green = not green
        return True

    def to_xml(self) -> Element:
        """
        :return: XML Element representation of TrafficLights including its history of phases
        """
        logic: Element = super().to_xml()
        for phases in self.history:
            for phase in phases:
                logic.append(Element("phase", {"duration": str(phase.duration), "state": phase.state}))
        return logic
