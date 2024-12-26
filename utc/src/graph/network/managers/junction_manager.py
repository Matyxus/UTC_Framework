from utc.src.graph.network.managers.container import Container, deepcopy
from utc.src.graph.network.parts import Junction, Route, Edge
from typing import Dict, Set, List, Tuple, Optional, Union, Iterable


class JunctionManager:
    """
    Class managing junctions for graphs, provides utility methods
    """
    def __init__(self):
        super().__init__()
        self.junctions: Dict[str, Junction] = {}
        self._junction_container: Container = Container(Junction, self.junctions)
        self.starting_junctions: Set[str] = set()
        self.ending_junctions: Set[str] = set()

    # -------------------------------------------- Junctions --------------------------------------------

    def add_junction(self, junction: Junction, replace: bool = False) -> bool:
        """
        :param junction: to be added
        :param replace: True if junction should be replaced (in case it already exists), False by default
        :return: True on success, false otherwise
        """
        if not self._junction_container.add_object(junction, replace):
            return False
        # Add to starting / ending junctions
        self.check_fringe(junction)
        return True

    def remove_junction(self, junction: Union[int, str, Junction]) -> bool:
        """
        Removes junctions including its routes (also from its neighbours),
        re-checks neighbouring junctions for possible new starting and/or ending junctions.

        :param junction: to be removed
        :return: True on success, false otherwise
        """
        # Check existence
        junction: Junction = self.get_junction(junction)
        if junction is None:
            return False
        # Remove from starting/ending junctions
        if junction.get_id() in self.starting_junctions:
            self.starting_junctions.remove(junction.get_id())
        if junction.get_id() in self.ending_junctions:
            self.ending_junctions.remove(junction.get_id())
        return self._junction_container.remove_object(junction)

    def junction_exists(self, junction: Union[int, str, Junction], message: bool = True) -> bool:
        """
        :param junction: id (internal or original) of junction or class instance
        :param message: True if message about missing junction should be printed, True by default
        :return: True if junction exists, false otherwise
        """
        return self._junction_container.object_exists(junction, message)

    # -------------------------------------------- Getters --------------------------------------------

    def get_neighbourhood_matrix(self) -> Dict[str, Tuple[Set[str], Set[str]]]:
        """
        :return: Matrix mapping junction ids to sets of their neighbours (incoming, outgoing)
        """
        return {
            junction.id: (junction.get_in_neighbours(), junction.get_out_neighbours())
            for junction in self.junctions.values()
        }

    def get_inner_junctions(self) -> List[Junction]:
        """
        :return: Junctions which are inside the network (not on fringe)
        """
        return [
            self.junctions[junction_id] for junction_id in
            (self.junctions.keys() ^ (self.starting_junctions | self.ending_junctions))
        ]

    def get_fringe_junctions(self) -> List[Junction]:
        """
        :return: Junctions which are on the fringe (starting and/or ending)
        """
        return self.get_junctions(list(self.starting_junctions | self.ending_junctions))

    def get_junctions(
            self, junctions: Iterable[Union[str, int, Junction]],
            message: bool = True, filter_none: bool = False
        ) -> List[Optional[Junction]]:
        """
        :param junctions: of graph (string - original, or int for internal representation)
        :param message: True if message about missing object should be printed, True by default
        :param filter_none: True if None values should be filtered out of list, False by default
        :return: List of Junction instances (Some can be None if any given junction does not exist)
        """
        return self._junction_container.get_objects(junctions, message, filter_none)

    def get_junction(self, junction: Union[str, int, Junction]) -> Optional[Junction]:
        """
        :param junction: of graph (string - original, or int for internal representation)
        :return: Junction object, None if given Junction does not exist
        """
        return self._junction_container.get_object(junction)

    def get_edges_connections(self, junctions: Iterable[Union[str, int, Junction]] = None) -> Dict[str, Set[str]]:
        """
        Iterates over all junctions and their current connections (represented by routes),
        to create mapping between edges

        :param junctions: Junctions over which we want to create edge mapping, if None all Junctions are taken
        :return: Mapping of edges connections {to_edge_id: [incoming_edge_id, ..], ..}
        """
        edges_connections: Dict[str, Set[str]] = {}

        def unpack(in_route: Optional[Route], out_route: Optional[Route]) -> Dict[str, Set[str]]:
            """
            :param in_route: 
            :param out_route: 
            :return: 
            """
            ret_val: Dict[str, Set[str]] = {}
            edge_sequence: List[Edge] = []
            if in_route is None and out_route is None:
                raise ValueError("Expected routes to be unpacked to be class instances, got 'None'!")
            elif in_route is None:
                edge_sequence = out_route.edge_list
            elif out_route is None:
                edge_sequence = in_route.edge_list
            else:
                edge_sequence = in_route.edge_list + out_route.edge_list
            # No mapping between edges
            if len(edge_sequence) == 0:
                return ret_val
            # Construct mapping between edges from routes
            for index in range(len(edge_sequence) - 1):
                to_edge_id: str = edge_sequence[index+1].get_id()
                from_edge_id: str = edge_sequence[index].get_id()
                if to_edge_id not in ret_val:
                    ret_val[to_edge_id] = set()
                ret_val[to_edge_id].add(from_edge_id)
            return ret_val

        def merge_mappings(mapping: Dict[str, Set[str]]) -> None:
            """
            :param mapping:
            :return:
            """
            for to_edge, from_edges in mapping.items():
                if to_edge not in edges_connections:
                    edges_connections[to_edge] = from_edges
                else:
                    edges_connections[to_edge] |= from_edges
            return
        # Create connections between edges from given Junctions (or all Junctions)
        junctions = self.get_junctions(junctions) if junctions is not None else self.junctions.values()
        for junction in junctions:
            for incoming_route, out_going_routes in junction.connections.items():
                if not out_going_routes:
                    merge_mappings(unpack(incoming_route, None))
                for out_route in out_going_routes:
                    merge_mappings(unpack(incoming_route, out_route))
        return edges_connections

    def get_junctions_list(self) -> List[Junction]:
        """
        :return: List of Junction classes
        """
        return list(self.junctions.values())

    # -------------------------------------------- Utils --------------------------------------------

    def check_fringe(self, junction: Junction) -> None:
        """
        :param junction: to be checked for being on the fringe (starting and/or ending)
        :return: None
        """
        if not self.junction_exists(junction):
            return
        start, end = junction.is_starting(), junction.is_ending()
        if start and end:
            self.starting_junctions.add(junction.get_id())
            self.ending_junctions.add(junction.get_id())
        elif start:
            self.starting_junctions.add(junction.get_id())
        elif end:
            self.ending_junctions.add(junction.get_id())
        elif not start and junction.get_id() in self.starting_junctions:
            self.starting_junctions.remove(junction.get_id())
        elif not end and junction.get_id() in self.ending_junctions:
            self.ending_junctions.remove(junction.get_id())
        return

    def construct_route(self, path: List[str]) -> Optional[Route]:
        """
        :param path: list of Junction ids on path
        :return: None in case path is empty or does not exist, Route otherwise
        """
        # Checks
        if len(path) == 0:
            print(f"Cannot construct path from empty list!")
            return None
        elif any(junction is None for junction in self.get_junctions(path)):
            return None
        ret_val: Route = Route([])
        in_route: Optional[Route] = None
        for i in range(0, len(path)-1):
            follow_route: Route = self.find_route(path[i], path[i+1], from_route=in_route)
            if follow_route is None:
                return ret_val
            in_route = follow_route
            ret_val |= follow_route
        return ret_val

    def find_route(self, from_junction_id: str, to_junction_id: str, from_route: Route = None) -> Optional[Route]:
        """
        :param from_route: optional parameter, incoming route to starting junction
        :param from_junction_id: starting junction
        :param to_junction_id: target junction (must be neighbour)
        :return: Route between junctions, None if it doesn't exist
        """
        if not self.junction_exists(from_junction_id) or not self.junction_exists(to_junction_id):
            return None
        for route in (
                self.junctions[from_junction_id].travel(from_route) if from_route is not None
                else self.junctions[from_junction_id].get_out_routes()
            ):
            if route.get_destination() == to_junction_id:
                return route
        print(f"Unable to find path between junctions: '{from_junction_id}' & '{to_junction_id}', given: {from_route}")
        return None

    def load_junctions(self, other: 'JunctionManager') -> bool:
        """
        :param other: JunctionManager class
        :return: True on success, false otherwise
        """
        # Checks
        if not isinstance(other, JunctionManager):
            print(f"Cannot load junctions from other objects, expected: 'JunctionManager', got: '{type(other)}' !")
            return False
        elif not self._junction_container.load(other._junction_container):
            return False
        self.starting_junctions = deepcopy(other.starting_junctions)
        self.ending_junctions = deepcopy(other.ending_junctions)
        return True
