from utc.src.graph.network import RoadNetwork, Junction, Route
from utc.src.routing.pddl.base.pddl_vehicle import PddlVehicle
from utc.src.simulator.vehicle import VehicleEntry
from utc.src.routing.pddl.info.episode_info import VehicleInfo
from typing import Optional, Dict, Tuple, List


class VehicleContainer:
    """
    Container of pddl vehicle classes, provides utility methods
    """
    def __init__(self, entry: VehicleEntry):
        """
        :param entry: vehicle entry
        """
        # Main objects of pddl problems
        self.network: Optional[RoadNetwork] = None
        # Vehicles
        self.vehicles: Dict[str, PddlVehicle] = {vehicle.id: PddlVehicle(vehicle, route) for vehicle, route in entry}
        self.vehicle_abstraction: Dict[str, str] = {}  # Mapping of: pddl_id -> vehicle_id
        self.info: VehicleInfo = VehicleInfo()

    def schedule_task(self) -> bool:
        """
        Checks vehicles, finds those that will be used for planning (their route
        is in the given network)

        :return: True on success, false otherwise
        """
        if not self.vehicles:
            print("No vehicles found in vehicle entry !")
            return False
        elif self.network is None:
            print("Handler received RoadNetwork of type 'None' !")
            return False
        self.info.total = len(self.vehicles)
        for i, (vehicle_id, pddl_vehicle) in enumerate(self.vehicles.items()):
            assert(pddl_vehicle.check_vehicle())
            # Vehicle was not scheduled for planning (due to error, or too short path etc.)
            if not pddl_vehicle.is_planned():
                continue
            # Vehicle will be used for planning
            # Vehicle graph route edges do not have to be in graph (since TopKA* found another)
            assert(None not in self.get_route_points(pddl_vehicle.graph_route))
            assert(None not in self.network.get_edges(pddl_vehicle.sub_graph))
            pddl_vehicle.pddl_id = f"v{i}"
            self.vehicle_abstraction[pddl_vehicle.pddl_id] = vehicle_id
        self.info.scheduled = len(self.vehicle_abstraction)
        print(f"{self.info.scheduled}/{self.info.total} vehicles are scheduled for planning")
        return True

    # ----------------------------------------------- Getters -----------------------------------------------

    def get_route_points(self, route: Route) -> Optional[Tuple[Junction, Junction]]:
        """
        :param route: related to vehicle
        :return: Points (starting and ending junction) of route, None if error occurred
        """
        return (
            self.network.get_junction(route.first_edge().from_junction),
            self.network.get_junction(route.last_edge().to_junction)
        )

    def get_occupied_edges(self) -> Dict[str, int]:
        """
        :return: Edges id mapped to number of vehicles
        (which have not been scheduled for planning)
        on them -> servers as capacity
        """
        occupied: Dict[str, int] = {}
        # Iterate over vehicles which are not being planned
        for vehicle_id, pddl_vehicle in self.vehicles.items():
            if pddl_vehicle.is_planned() or pddl_vehicle.graph_route is None:
                continue
            # For each edge vehicle goes trough on the network increase capacity
            for edge_id in (set(pddl_vehicle.graph_route.get_edge_ids()) & self.network.edges.keys()):
                occupied[edge_id] = occupied.get(edge_id, 0) + 1
        return occupied

    def get_planned_vehicles(self) -> List[PddlVehicle]:
        """
        :return: PddlVehicle classes, which are scheduled for planning
        """
        return [pddl_vehicle for pddl_vehicle in self.vehicles.values() if pddl_vehicle.is_planned()]

    def get_vehicle(self, vehicle_id: str) -> Optional[PddlVehicle]:
        """
        :param vehicle_id: id of vehicle, can be original or pddl id
        :return: PddlVehicle if it exists, None otherwise
        """
        return self.vehicles.get(self.vehicle_abstraction.get(vehicle_id, vehicle_id), None)
