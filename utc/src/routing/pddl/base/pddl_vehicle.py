from utc.src.simulator.vehicle import Vehicle
from utc.src.graph import Route
from xml.etree.ElementTree import Element
from typing import Optional, Tuple, List, FrozenSet


class PddlVehicle:
    """
    Class representing vehicle for pddl problems,
    holds the necessary objects which are needed to
    represent it in pddl format.
    """
    def __init__(self, vehicle: Vehicle, original_route: Element):
        """
        :param vehicle: extracted from routes file
        :param original_route: route of vehicle extracted from routes file
        """
        # Routes file
        self.vehicle: Vehicle = vehicle
        self.original_route: Element = original_route
        # Pddl vars
        self.pddl_id: str = ""  # Id of vehicle in pddl file
        self.graph_route: Optional[Route] = None  # Route on graph
        self.indexes: Tuple[int, int] = (0, -1)  # Range of edges from original route to graph route
        self.sub_graph: Optional[FrozenSet[int]] = None  # Id's of routes, vehicle is allowed to drive on
        # Starting junction is set by NetworkDomain, since it is unknown if vehicle is on split junction or not
        self.starting_junction: str = ""
        self.ending_junction: str = ""
        self.allowed_starting: Optional[Tuple[int, ...]] = None  # Allowed routes on which vehicle can start
        self.allowed_ending: Optional[Tuple[int, ...]] = None  # Allowed routes on which vehicle can end

    # -------------------------------------- Setters --------------------------------------

    def set_graph_route(self, route: Route, indexes: Tuple[int, int] = (0, -1)) -> None:
        """
        :param route: route on graph
        :param indexes: range of subsequence of original route edges (by default whole route)
        :return: None
        """
        assert(" ".join(route.get_edge_ids()) in self.original_route.attrib["edges"])
        self.graph_route = route
        self.indexes = indexes

    # -------------------------------------- Utils --------------------------------------

    def is_planned(self) -> bool:
        """
        :return: True if vehicle is scheduled for planning, false otherwise
        """
        return None not in (self.sub_graph, self.graph_route)

    def check_vehicle(self) -> bool:
        """
        :return:
        """
        if self.original_route is None or self.vehicle is None:
            print("Received invalid vehicle or original route in PddlVehicle!")
            return False
        # Vehicle does not drive on any network
        elif self.graph_route is None:
            return True
        # Check graph route against original
        original_edges: List[str] = self.original_route.attrib["edges"].split()
        return original_edges[self.indexes[0]:self.indexes[1]] == self.graph_route.get_edge_ids()

