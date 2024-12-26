from utc.src.graph import RoadNetwork
from utc.src.simulator.vehicle import Vehicle, VehicleEntry
from utc.src.simulator.simulation import Simulation, traci
from copy import deepcopy
from typing import Optional, List, Set, Tuple, Dict


class SumoVehicle(Vehicle):
    """
    Vehicle class to represent vehicle in SUMO.
    """
    def __init__(self, attributes: Dict[str, str], route: Tuple[str], departed: float):
        super().__init__(attributes)
        self.route: Tuple[str] = route
        self.departed: float = departed
        # Vehicle can have multiple eta's due to arriving at multiple regions
        self.eta: List[float] = []
        self.arrived: float = -1
        # Vehicle visits of regions (regionID, routeIndex)
        self.visits: List[Tuple[int, int]] = []
        self.current_visit: int = -1

    def add_eta(self, eta: float) -> None:
        """
        :param eta:
        :return:
        """
        assert(eta > 0)
        self.eta.append(eta)

    def add_visit(self, region_id: int, route_index: int) -> None:
        """
        :param region_id:
        :param route_index:
        :return:
        """
        self.visits.append((region_id, route_index))

    def get_expected_arrival(self) -> float:
        """
        :return:
        """
        if not self.eta:
            print(f"Error, vehicle: '{self.id}' does not have an ETA!")
            return -1
        return self.departed + self.eta[-1]

    def get_current_visit(self) -> Tuple[int, float]:
        """
        :return: The current region visited by vehicle and the ETA
        """
        if not self.visits or self.current_visit == -1:
            print(f"Error, vehicle: '{self.id}' was not assigned visited regions!")
            return -1, -1
        return self.visits[self.current_visit][0], self.get_expected_arrival()

    def get_current_route(self, index: int) -> Tuple[int]:
        """
        :return: The current sub-route to region
        """
        assert((0 <= index <= len(self.route)) and self.current_visit != -1)
        return self.route[index:self.visits[self.current_visit][1]]




class VehicleQueue:
    """
    Class holding vehicles in different queues from running simulation.
    """
    def __init__(self):
        self.vehicles: Dict[str, SumoVehicle] = {}
        self.running: Set[str] = set()  # Vehicle currently running in simulation
        self.scheduled: Set[str] = set()  # Vehicle currently considered for planning
        self.arrived: Set[str] = set()  # Vehicles which already left the simulation
        self.planned: Set[str] = set()  # Vehicles which were planned

    def remove_schedule(self, vehicle: SumoVehicle, time: float) -> None:
        """
        :param vehicle:
        :param time:
        :return:
        """
        assert(vehicle.id in self.scheduled)
        print(f"Vehicle: '{vehicle.id}' arrived to region before plan was made, by: "
              f"{round(abs(vehicle.get_expected_arrival() - time), 3)}[s]."
        )
        self.scheduled.remove(vehicle.id)
        if vehicle.current_visit + 1 == len(vehicle.visits):
            print("Vehicle does not visit any more regions, discarding it ...")
            self.vehicles.pop(vehicle.id)
        else:
            print("Vehicle moved back to running queue as it visits another region\s in future.")
            vehicle.current_visit += 1
            self.running.add(vehicle.id)
        return

    def set_arrival(self, vehicle_id: str, time: float) -> None:
        """
        :param vehicle_id:
        :param time:
        :return:
        """
        # Vehicle was not considered (does not go to the regions)
        if vehicle_id not in self.vehicles:
            return
        assert(vehicle_id not in self.arrived)
        assert(vehicle_id in self.running or vehicle_id in self.scheduled or vehicle_id in self.planned)
        self.arrived.add(vehicle_id)
        self.vehicles[vehicle_id].arrived = time
        if vehicle_id in self.running:
            print(f"Vehicle: '{vehicle_id}' arrived at destination, but was not scheduled!")
            self.running.remove(vehicle_id)
            return
        elif vehicle_id in self.scheduled:
            diff: float = round(abs(self.vehicles[vehicle_id].get_expected_arrival() - time), 3)
            print(f"Vehicle: '{vehicle_id}' arrived at destination earlier than expected by: {diff}[s] !")
            self.scheduled.remove(vehicle_id)
            return
        # Else Already planned
        return


class Scheduler:
    """
    Class scheduling vehicles from running simulation for online planning.
    """
    def __init__(self, regions: List[RoadNetwork], interval: Tuple[float, float, float]):
        """
        :param regions:
        :param interval:
        """
        self.regions: List[RoadNetwork] = regions
        self.interval: Tuple[float, float, float] = interval
        self.queue: VehicleQueue = VehicleQueue()

    def step(self, simulation: Simulation) -> bool:
        """
        :param simulation:
        :return:
        """
        if not simulation.is_running():
            return False
        # Process vehicles which arrived this time step
        for vehicle_id in traci.simulation.getArrivedIDList():
            self.queue.set_arrival(vehicle_id, simulation.get_time())
        # Process vehicles which just arrived this time step, add them to queue
        for vehicle_id in traci.simulation.getDepartedIDList():
            pass
        # For each scheduled vehicle, check if they have not yet arrived to region
        for vehicle_id in self.queue.scheduled:
            vehicle: SumoVehicle = self.queue.vehicles[vehicle_id]
            region_id, _ = vehicle.get_current_visit()
            # Vehicle already arrived, sooner then plan was generated, remove schedule
            if traci.vehicle.getRoadID(vehicle_id) in self.regions[region_id].edges:
                self.queue.remove_schedule(vehicle, simulation.get_time())
        return True

    # def assign_routes(self, ):

    # ------------------------------------------- Vehicle arrival -------------------------------------------


    # 3 Problems of vehicle arrival:
    # 1) Left simulation -> discard vehicle
    # 2) Vehicle arriving sooner/later than expected, check interval then decide
    # 3) Vehicle arrived prior to even ETA being decided, reschedule for later if possible

    def check_arrival(self, vehicle_id: str, time: float) -> None:
        """
        :param vehicle_id: id of the vehicle
        :param time: current time
        :return:
        """
        # Vehicle was discarded from routing (does not go to the regions)
        if vehicle_id not in self.queue.vehicles:
            return
        # Make sure that vehicle is still in simulation
        assert(vehicle_id not in self.queue.arrived)
        vehicle: SumoVehicle = self.queue.vehicles[vehicle_id]
        scheduled: bool = (vehicle_id in self.queue.scheduled)
        running: bool = (vehicle_id in self.queue.running)
        in_region: bool = ()
        # Check if vehicle arrived earlier than expected



        # Check if vehicle has not arrived withing provided time




        return



    # ------------------------------------------- Utils -------------------------------------------

    def compute_etas(self, network: RoadNetwork, simulation: Simulation) -> bool:
        """
        :param network:
        :return:
        """
        if not simulation.is_running():
            return False
        # Update average travel time on edges
        for edge in network.edges.values():
            edge.attributes["travelTime"] = (edge.attributes["travelTime"] + traci.edge.getTraveltime(edge)) / 2
        # Update ETA's of vehicles based on new information
        for vehicle_id in self.queue.running:
            vehicle: SumoVehicle = self.queue.vehicles[vehicle_id]
            current: int = traci.vehicle.getRoadID(vehicle_id)
            if current >= vehicle.visits[vehicle.current_visit][1]:
                diff: float = round(abs(vehicle.get_expected_arrival()), 3)
                print(f"Vehicle '{vehicle_id}' arrived to region earlier than expected by: {diff} [s]")
            else:
                vehicle.set_eta(sum(
                    [edge.attributes["travelTime"] for edge in network.get_edges(vehicle.get_current_route(current))]
                ))
            # If vehicle ETA is within expected interval, consider it for scheduling



        return True














