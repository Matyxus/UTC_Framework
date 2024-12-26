from utc.src.graph import RoadNetwork, Route
from utc.src.simulator.vehicle.vehicle import Vehicle
from xml.etree.ElementTree import Element
from typing import Dict, Tuple


class VehicleEntry:
    """
    Class representing multiple vehicles in given time interval
    and their routes (ones extracted from Network or routes files)
    """
    def __init__(self, interval: Tuple[float, float] = None):
        """
        :param interval: in which vehicles are arriving in the network
        """
        self.vehicles: Dict[str, Vehicle] = {}
        # Routes extracted from SumoRoutesFile
        self.original_routes: Dict[str, Element] = {}
        # Routes on graph
        self.graph_routes: Dict[str, Tuple[Route, Tuple[int, int]]] = {
            # route_id (same as original route) : (Route, (left, right))
            # (left, right) -> indexes in case Route is sub_route of original
        }
        self.interval: Tuple[float, float] = interval

    # ---------------------------------- Adders ----------------------------------

    def add_vehicle(self, vehicle: Vehicle) -> None:
        """
        :param vehicle: extracted from SumoVehicles file or generated
        :return: None
        """
        self.vehicles[vehicle.attributes["id"]] = vehicle

    def add_original_route(self, original_route: Element) -> None:
        """
        :param original_route: extracted from SumoRoutes file
        :return: None
        """
        self.original_routes[original_route.attrib["id"]] = original_route

    def add_graph_route(self, identifier: str, graph_route: Route, indexes: Tuple[int, int] = None) -> None:
        """
        :param identifier: of route (since Route object is always temporary when assigned as such)
        :param graph_route: route from graph
        :param indexes: of route, in case it is sub-route of original route (route on subgraph)
        :return: None
        """
        self.graph_routes[identifier] = (graph_route, indexes)

    # ---------------------------------- Setters ----------------------------------

    def set_interval(self, interval: Tuple[float, float]) -> None:
        """
        :param interval: in which vehicles are arriving in the network
        :return: None
        """
        self.interval = interval

    # ---------------------------------- Utils ----------------------------------

    def get_scenario_routes(self) -> Dict[Element, Element]:
        """
        :return:
        """
        return {vehicle.to_xml(): self.original_routes[vehicle.attributes["route"]] for vehicle in self.vehicles.values()}

    def generate_routes(self, network: RoadNetwork) -> bool:
        """
        Generates Routes from original routes of vehicles extracted from file

        :param network: road network on which vehicles will drive (can be sub-graph)
        :return: True on success, False otherwise
        """
        print(f"Generating graph routes for vehicle entry!")
        if network is None:
            print(f"Cannot generate routes for vehicles on route of type 'None' !")
            return False
        # Create new route for each vehicle from its original route, that drives on network
        for vehicle in self.vehicles.values():
            original_route: Element = self.original_routes.get(vehicle.attributes["route"], None)
            if original_route is None:
                print(f"Vehicle {vehicle.attributes['id']} is missing route: {vehicle.attributes['route']} !")
                return False
            edges, index = network.get_longest_sequence(original_route.attrib["edges"].split())
            if not edges:
                print(f"Vehicle: {vehicle.attributes['id']} does not drive on network: {network.name}")
                continue
            self.add_graph_route(original_route.attrib["id"], Route(edges), index)
            assert (original_route.attrib["edges"].split()[index[0]:index[1]] == self.graph_routes[original_route.attrib["id"]][0].get_edge_ids())
        return True

    # ---------------------------------- Magics ----------------------------------

    def __str__(self) -> str:
        """
        :return: String representation of vehicle entry
        """
        return (
            f"Vehicle entry, vehicles: {len(self.vehicles)} from interval: {self.interval} " +
            f"original routes: {len(self.original_routes)} graph routes: {len(self.graph_routes)}"
        )

    def __iter__(self) -> Tuple[Vehicle, Element]:
        """
        :return: Vehicle and its route as tuple
        """
        for vehicle in self.vehicles.values():
            yield vehicle, self.original_routes[vehicle.attributes["route"]]
