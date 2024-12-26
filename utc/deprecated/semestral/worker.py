from utc.src.semestral.evolutionary import Population
from utc.src.simulator import Simulation
from utc.src.semestral.traffic_lights import TrafficLights
from typing import Optional, Union, Tuple, List
from multiprocessing import current_process
import traci


def evaluate(
        population: Union[List[Population], Population],
        traffic_lights: List[TrafficLights],
        config: str, options: dict,
        end_time: float, new_state: str = ""
    ) -> Optional[List[Tuple[float, int]]]:
    """
    Evaluates population, starts new simulation for each population,
    can be used to run on multiple processes.

    :param population: population to be evaluated
    :param traffic_lights: traffic lights defined for population
    :param config: configuration file
    :param options: options which should be loaded with simulation (state and begin options are added automatically)
    :param end_time: time at which simulation should end at
    :param new_state: file path of new state (if one should be made, default None)
    :return: List containing pairs of (waiting time, number of vehicles which left simulation)
    """
    print(f"Evaluation population on process: {current_process().name}")
    if isinstance(population, Population):
        population = [population]
    # Checks
    if not population:
        print(f"Got invalid or empty population: {population}")
        return None
    elif not options:
        print("Got empty options!")
        return None
    elif not traffic_lights:
        print("Got empty list of traffic lights!")
        return None
    elif traci.isLoaded():
        print("Traci is already loaded on process, closing connection ...")
        traci.close()
    # For each population start simulation and evaluate
    results: List[Tuple[float, int]] = []
    for pop in population:
        waiting_time: float = 0
        arrived: int = 0
        departed: int = 0
        # We do not need to load main simulation to current state, as it is there always
        # print(f"Running simulation up to time: {end_time}")
        with Simulation(config, options) as sim:
            if sim is None:
                return None
            # Update traffic lights in current simulation
            for i, indiv in enumerate(pop.pops):
                # Set the duration of base program to 0
                traffic_lights[i].update_tl(indiv)
            # Calculate values
            while sim.is_running(use_end_time=True) and sim.get_time() < end_time:
                sim.step()
                # Measure waiting time: https://github.com/eclipse-sumo/sumo/issues/11867
                for vehicle_id in traci.vehicle.getIDList():
                    if traci.vehicle.getSpeed(vehicle_id) < 0.1:
                        waiting_time += sim.config.get_step_length()
                # Count number of vehicles leaving and arriving in the network (in current time step)
                arrived += traci.simulation.getArrivedNumber()
                departed += traci.simulation.getDepartedNumber()
            if new_state:
                # Save the best TL states (phases) and calculate next phase
                for traffic_light in traffic_lights:
                    traffic_light.save_state()
                print(f"Saving simulation state: {new_state}")
                traci.simulation.saveState(new_state)
            # print()
            # print(f"(Arrived, departed, running) vehicles: {arrived, departed, len(traci.vehicle.getIDList())}")
            # print(f"Waiting time total: {waiting_time}, average: {round(waiting_time / departed, 2)}")
            # print(f"Simulation time: {sim.get_time()}")
        results.append((waiting_time, arrived))
    return results


def sim_evaluate(config: str, options: dict, end_time: float) -> Optional[Tuple[float, int]]:
    """
    Evaluates given configuration file

    :param config: configuration file
    :param options: options which should be loaded with simulation (state and begin options are added automatically)
    :param end_time: time at which simulation should end at
    :return: List containing pairs of (waiting time, number of vehicles which left simulation)
    """
    print(f"Evaluation population on process: {current_process().name}")
    print(f"End_time: '{end_time}'")
    # Checks
    if not options:
        print("Got empty options!")
        return None
    elif traci.isLoaded():
        print(f"Traci is already loaded on process, closing connection ...")
        traci.close()
    # For each population start simulation and evaluate
    waiting_time: float = 0
    arrived: int = 0
    departed: int = 0
    # We do not need to load main simulation to current state, as it is there always
    # print(f"Running simulation up to time: {end_time}")
    with Simulation(config, options) as sim:
        if sim is None:
            return None
        # Calculate values
        while sim.is_running(use_end_time=True) and sim.get_time() < end_time:
            sim.step()
            # Measure waiting time: https://github.com/eclipse-sumo/sumo/issues/11867
            for vehicle_id in traci.vehicle.getIDList():
                if traci.vehicle.getSpeed(vehicle_id) < 0.1:
                    waiting_time += sim.config.get_step_length()
            # Count number of vehicles leaving and arriving in the network (in current time step)
            arrived += traci.simulation.getArrivedNumber()
            departed += traci.simulation.getDepartedNumber()
        print()
        print(f"(Arrived, departed, running) vehicles: {arrived, departed, len(traci.vehicle.getIDList())}")
        print(f"Waiting time total: {waiting_time}, average: {round(waiting_time / departed, 2)}")
        print(f"Simulation time: {sim.get_time()}")
    return waiting_time, arrived


def sim_log(config: str, options: dict, end_time: float) -> Optional[List[float]]:
    """
    Evaluates given configuration file for each time step

    :param config: configuration file
    :param options: options which should be loaded with simulation (state and begin options are added automatically)
    :param end_time: time at which simulation should end at
    :return: List containing average waiting time calculated each time step
    """
    print(f"Evaluation population on process: {current_process().name}")
    print(f"End_time: '{end_time}'")
    # Checks
    if not options:
        print("Got empty options!")
        return None
    elif traci.isLoaded():
        print(f"Traci is already loaded on process, closing connection ...")
        traci.close()
    results: List[float] = []
    # For each population start simulation and evaluate
    waiting_time: float = 0
    arrived: int = 0
    departed: int = 0
    # We do not need to load main simulation to current state, as it is there always
    # print(f"Running simulation up to time: {end_time}")
    with Simulation(config, options) as sim:
        if sim is None:
            return None
        # Calculate values
        while sim.is_running(use_end_time=True) and sim.get_time() < end_time:
            sim.step()
            # Measure waiting time: https://github.com/eclipse-sumo/sumo/issues/11867
            for vehicle_id in traci.vehicle.getIDList():
                if traci.vehicle.getSpeed(vehicle_id) < 0.1:
                    waiting_time += sim.config.get_step_length()
            # Count number of vehicles leaving and arriving in the network (in current time step)
            arrived += traci.simulation.getArrivedNumber()
            departed += traci.simulation.getDepartedNumber()
            if arrived == 0:
                results.append(0)
            else:
                results.append(round(waiting_time / departed, 2))
        print()
        print(f"(Arrived, departed, running) vehicles: {arrived, departed, len(traci.vehicle.getIDList())}")
        print(f"Waiting time total: {waiting_time}, average: {round(waiting_time / departed, 2)}")
        print(f"Simulation time: {sim.get_time()}")
    return results



