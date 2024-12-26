from utc.src.graph.network.parts.edge import XmlObject, Edge
from utc.src.constants.static.pddl_constants import NetworkCapacity
from typing import List, Tuple, Dict, Union, Optional


class Route(XmlObject):
    """ Route is class holding edges, trough which the route goes """

    def __init__(
            self, edges: Union[List[Edge], Edge], identifier: str = "TEMPORARY",
            internal_id: int = -1, attributes: Dict[str, str] = None
        ):
        """
        :param edges: list of edges route goes through
        :param identifier: of object, original (given by user)
        :param internal_id: internal identifier of object
        :param attributes: additional attributes
        """
        super().__init__("route", identifier, internal_id, attributes)
        self.edge_list: List[Edge] = edges if isinstance(edges, list) else [edges]
        self.allowed_first: bool = True  # True if route is allowed in search, False otherwise
        self.allowed_last: bool = True
        if internal_id >= 0:
            assert (self.id != "" and self.id != "TEMPORARY")
            for edge in self.edge_list:
                edge.references += 1

    # --------------------------------------------- Getters ---------------------------------------------

    def get_start(self) -> Optional[str]:
        """
        :return: Id of Junction this Route starts at, None if edges are empty
        """
        if not self.is_valid():
            return None
        return self.first_edge().from_junction

    def get_destination(self) -> Optional[str]:
        """
        :return: Id of Junction this Route leads to, None if edges are empty
        """
        if not self.is_valid():
            return None
        return self.last_edge().to_junction

    def get_junctions(self) -> List[str]:
        """
        :return: List of junction id's route goes trough, empty if route is empty
        """
        if not self.is_valid():
            return []
        return [self.get_start()] + [edge.to_junction for edge in self.edge_list]

    def get_edge_ids(self, internal: bool = False) -> List[Union[str, int]]:
        """
        :param internal: True if internal id of edges should be returned, original otherwise
        :return: List of edge id's route goes trough, empty if route is empty
        """
        return [edge.get_id(internal) for edge in self.edge_list]

    def get_capacity(self) -> int:
        """
        :return: Capacity of route, 0 if route has no edges
        """
        if not self.is_valid():
            print(f"Route: {self} does not have any edges, cannot compute capacity!")
            return 0
        # Find how many lanes routes has, if there is edge with only 1 lane (capacity multiplier is 1)
        lane_multiplier: int = max(min([edge.get_lane_count() for edge in self.edge_list]), 1)
        # Route_length / (car_length + gap)
        capacity: int = max(int(self.traverse()[0] / (NetworkCapacity.CAR_LENGTH + NetworkCapacity.MIN_GAP)), 1)
        return capacity * lane_multiplier

    def get_average_traveling_time(self) -> float:
        """
        :return: The average time it takes to traverse the route in seconds (1 minimal), -1 if error occurred
        """
        if not self.is_valid():
            print(f"Route: {self} does not have any edges, cannot compute average traveling time!")
            return -1
        # route_length / average_speed
        return max(self.traverse()[0] / (sum([edge.speed for edge in self.edge_list]) / len(self.edge_list)), 1.0)

    def get_travel_time(self) -> float:
        """
        :return: The average observed travel time on the entire route (1 minimal), -1 if error occurred
        """
        if not self.is_valid():
            print(f"Route: {self} does not have any edges, cannot compute average traveling time!")
            return -1
        return sum([edge.attributes["travelTime"] for edge in self.edge_list])
    # ---------------------------- Utils ----------------------------

    def is_temporary(self) -> bool:
        """
        :return: True if Route is made for temporary purposes
        """
        return self.internal_id == -1

    def is_valid(self) -> bool:
        if len(self.edge_list) == 0:
            return False
        # Check if the edges are on correct path
        current_junction_id: str = self.edge_list[0].to_junction
        for i in range(1, len(self.edge_list)):
            if self.edge_list[i].from_junction != current_junction_id:
                print(f"Found edges that are not connect in route: {self}")
                return False
            current_junction_id = self.edge_list[i].to_junction
        return True

    def first_edge(self) -> Edge:
        """
        :return: Id of first edge on route
        """
        return self.edge_list[0]

    def last_edge(self) -> Edge:
        """
        :return: Id of last edge on route
        """
        return self.edge_list[-1]

    def has_edge(self, edge: Edge) -> bool:
        """
        :param edge: to be checked
        :return: True if route contains Edge, false otherwise
        """
        return edge in self.edge_list

    def traverse(self) -> Tuple[float, str]:
        """
        :return: Tuple containing length of route and its destination (as junction id)
        """
        return sum(edge.length for edge in self.edge_list), self.get_destination()

    def info(self, verbose: bool = True) -> str:
        ret_val: str = f"Route: {self.id}({self.internal_id}), from: {self.get_start()}, to: {self.get_destination()}"
        ret_val += f", edges: {self.get_edge_ids(False)}"
        return ret_val

    def to_xml(self):
        self.attributes["edges"] = " ".join(self.get_edge_ids())
        return super().to_xml()

    # --------------------------------------------- Magics ---------------------------------------------

    def __or__(self, other: 'Route') -> 'Route':
        """
        :param other: route to be merged with
        :return: self merged with other Route
        """
        if not isinstance(other, Route):
            raise TypeError(f"Cannot compare class: 'Route' with '{type(other)}' !")
        for edge in other.edge_list:
            self.edge_list.append(edge)
        return self

    def __ror__(self, other: 'Route') -> 'Route':
        """
        :param other: route to be merged with
        :return: self merged with other Route
        """
        return self.__or__(other)

    def __str__(self) -> str:
        return f"Route: {self.get_id()}, path: {[edge.get_id(False) for edge in self.edge_list]}"

