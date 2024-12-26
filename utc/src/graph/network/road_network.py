from utc.src.graph.network import Junction, Edge, Route
from utc.src.graph.network.managers import JunctionManager, EdgeManager, RouteManager
from typing import Dict, List, Set, Optional, Union


class RoadNetwork(JunctionManager, EdgeManager, RouteManager):
    """
    Container of graph objects, e.g. Junctions, Edges, Routes trough managers, provides utility methods.
    """
    def __init__(self, name: str = ""):
        """
        :param name: of network (optional parameter)
        """
        super().__init__()
        self.name: str = name
        self.map_name: str = ""  # Name of map network was loaded from
        self.roundabouts: List[List[str]] = []

    # -------------------------------------------------- Adders --------------------------------------------------

    def add_edge(self, edge: Edge, replace: bool = False) -> bool:
        """
        :param edge: to be added (must be added in order of their internal id's)
        :param replace: True if edge should be replaced (in case it already exists), False by default
        :return: True on success, false otherwise
        """
        if not (self.junction_exists(edge.from_junction) and self.junction_exists(edge.to_junction)):
            return False
        return super().add_edge(edge, replace)

    def add_route(self, route: Route, replace: bool = False) -> bool:
        if not all(self.edge_exists(edge) for edge in route.edge_list):
            return False
        return super().add_route(route, replace)

    # -------------------------------------------------- Removers --------------------------------------------------

    def remove_junction(
            self, junction: Union[str, int, Junction],
            edge_removal: bool = True, route_removal: bool = True
        ) -> bool:
        """
        :param junction: to be removed
        :param edge_removal: True if edges on each route in junction should be removed
        :param route_removal: True if routes junction has should be removed
        :return: True on success, false otherwise
        """
        # Check for existence
        junction: Optional[Junction] = self.get_junction(junction)
        if junction is None:
            return False
        # Remove outgoing routes first
        # Transform into set -> can have multiple same out-routes, coming from different in-routes
        if route_removal:
            for out_route in set(junction.get_out_routes()):
                if not self.remove_route(out_route, edge_removal):
                    return False
            # Remove incoming routes
            for in_route in junction.get_in_routes():
                if not self.remove_route(in_route, edge_removal):
                    return False
        return super().remove_junction(junction)

    def remove_edge(self, edge: Union[str, int, Edge], route_removal: bool = True) -> bool:
        """
        :param edge: to be removed (either class or id)
        :param route_removal: True if routes should be searched for edge removal, default True
        :return: True on success, false otherwise
        """
        # Check for existence
        edge: Optional[Edge] = self.get_edge(edge)
        if edge is None:
            return False
        # Find all routes containing this edge, remove them
        if route_removal and edge.references != 0:
            for route in list(self.routes.values()):  # Convert to list to iterate and remove
                if route.has_edge(edge) and not self.remove_route(route):
                    return False
        # Edge may already be removed when corresponding route was removed
        return not self.edge_exists(edge, False) or super().remove_edge(edge)

    def remove_route(self, route: Union[str, int, Route], edge_removal: bool = True) -> bool:
        """
        :param route: to be removed
        :param edge_removal: True if edges should be searched for route removal, default True
        :return: True on success, false otherwise
        """
        route: Optional[Route] = self.get_route(route)
        if route is None or route.is_temporary():
            return False
        # Remove route from corresponding junctions
        start_junction: Junction = self.get_junction(route.get_start())
        end_junction: Junction = self.get_junction(route.get_destination())
        assert(self.junction_exists(start_junction) and self.junction_exists(end_junction))
        if not start_junction.remove_out_route(route):
            return False
        elif not end_junction.replace_in_route(route, None):
            return False
        elif not super().remove_route(route):
            return False
        # Check reference counter, remove edges with 0 references
        if edge_removal:
            for edge in route.edge_list:
                # If edge has 0 references, we do not need to search other routes
                if edge.references == 0 and not self.remove_edge(edge, False):
                    return False
        # Update junctions to be added or removed from starting/ending lists
        self.check_fringe(start_junction)
        self.check_fringe(end_junction)
        return True

    # --------------------------------------------- Edge neighbours ---------------------------------------------

    def get_in_edge_neighbours(self, edge: Union[int, str, Edge]) -> Optional[List[Edge]]:
        """
        :param edge: from which to find connections
        :return: List of edges coming to given edge, can be empty, None if error occurred
        """
        # Checks
        edge: Optional[Edge] = self.get_edge(edge)
        if edge is None:
            return None
        from_junction: Optional[Junction] = self.get_junction(edge.from_junction)
        if from_junction is None:
            return None
        # Find incoming edges to this edge
        ret_val: Set[Edge] = set()
        for in_route in from_junction.get_in_routes():
            for out_route in from_junction.travel(in_route):
                if out_route.first_edge().id == edge.id:
                    ret_val.add(in_route.last_edge())
        # assert(len(ret_val) != 0)
        return list(ret_val)

    def get_out_edge_neighbours(self, edge: Union[int, str, Edge]) -> Optional[List[Edge]]:
        """
        :param edge: from which to find connections
        :return: List of edges going from given edge, can be empty, None if error occurred
        """
        # Checks
        edge: Optional[Edge] = self.get_edge(edge)
        if edge is None:
            return None
        to_junction: Optional[Junction] = self.get_junction(edge.to_junction)
        if to_junction is None:
            return None
        # Find route which represents this edge (there must be exactly one)
        in_route: Optional[Route] = None
        for incoming_route in to_junction.get_in_routes():
            if incoming_route.last_edge().id == edge.id:
                in_route = incoming_route
                break
        assert(in_route is not None)
        # Find out-going edges from this edge
        return list(set([out_route.first_edge() for out_route in to_junction.travel(in_route)]))

    def get_edge_neighbours(self, edge: Union[int, str, Edge]) -> Optional[List[Edge]]:
        """
        :param edge: from which to find connections
        :return: List of edges connected to given edge, can be empty, None if error occurred
        """
        in_connections: Optional[List[Edge]] = self.get_in_edge_neighbours(edge)
        out_connections: Optional[List[Edge]] = self.get_out_edge_neighbours(edge)
        return None if (in_connections is None or out_connections is None) else (in_connections + out_connections)

    # -------------------------------------------------- Utils --------------------------------------------------

    def load(self, other: 'RoadNetwork') -> bool:
        """
        Loads skeleton from another skeleton class (deep copy)

        :param other: RoadNetwork class (loaded from the same file)
        :return: True on success, false otherwise
        """
        if not isinstance(other, RoadNetwork):
            print(f"Can only load RoadNetwork class from other RoadNetwork class, got: '{type(other)}' !")
            return False
        # Load containers
        elif not self.load_junctions(other):
            return False
        elif not self.load_edges(other):
            return False
        elif not self.load_routes(other):
            return False
        self.name = other.name
        self.map_name = other.map_name
        self.roundabouts = [] + other.roundabouts
        return True

    # -------------------------------------------- Set Operators --------------------------------------------

    def intersection(self, other: 'RoadNetwork') -> Optional['RoadNetwork']:
        """
        Performs set intersection on RoadNetwork classes (graphs of road networks), based on objects id's.

        :param other: RoadNetwork class, must have at least 1 common junction
        :return: New skeleton class, None if error occurred
        """
        if not isinstance(other, RoadNetwork):
            print(f"Graph intersection operation expects 'other' to be of type 'RoadNetwork', got: '{type(other)}'")
            return None
        # Get common Junctions, remove others
        common_junctions: Set[str] = self.junctions.keys() & other.junctions.keys()
        if not common_junctions:  # Empty
            print(f"Cannot perform intersection on RoadNetworks, no common junctions found !")
            return None
        # Prepare new Graph
        ret_val: RoadNetwork = RoadNetwork()
        ret_val.load(self)
        # Remove other junctions
        for junction_id in (self.junctions.keys() ^ common_junctions):
            ret_val.remove_junction(junction_id)
        return ret_val

    def union(self, other: 'RoadNetwork') -> Optional['RoadNetwork']:
        """
        Performs set union on RoadNetwork classes (graphs of road networks), based on objects id's.

        :param other: RoadNetwork class, must have at least one common junction
        :return: New RoadNetwork class, None if error occurred
        """
        if not isinstance(other, RoadNetwork):
            print(f"Graph union operation expects 'other' to be of type 'RoadNetwork', got: '{type(other)}'")
            return None
        elif not (self.edges.keys() & other.edges.keys()):
            print(f"Graph union cannot be executed, graphs have no common edge!")
            return None
        raise NotImplementedError("Error, union of graphs is not implemented!")

    def difference(self, other: 'RoadNetwork') -> Optional['RoadNetwork']:
        """
        Performs set difference on RoadNetwork classes (graphs of road networks), based on objects id's.

        :param other: RoadNetwork class, must have at least one common junction
        :return: New skeleton class, None if error occurred
        """
        if not isinstance(other, RoadNetwork):
            print(f"Graph difference operation expects 'other' to be of type 'RoadNetwork', got: '{type(other)}'")
            return None
        # Prepare new Graph
        ret_val: RoadNetwork = RoadNetwork()
        ret_val.load(self)
        # Unite both together
        ret_val = ret_val.union(other)
        # Remove what is common for both graphs
        for common_junction_id in (self.junctions.keys() & other.junctions.keys()):
            ret_val.remove_junction(common_junction_id)
        return ret_val

    # -------------------------------------------------- Magics --------------------------------------------------

    def __eq__(self, other: 'RoadNetwork') -> bool:
        """
        :param other: Road network class to check against
        :return: True if road networks are the same, False otherwise
        """
        if not isinstance(other, RoadNetwork):
            print(f"Cannot check for equality between RoadNetwork and {type(other)}")
            return False
        if self.edges.keys() != other.edges.keys():
            print(f"Networks do not have the same edges!")
            return False
        elif self.junctions.keys() != other.junctions.keys():
            print(f"Networks do not have the same junctions!")
            return False
        edge_connections: Dict[str, Set[str]] = self.get_edges_connections()
        other_edge_connections: Dict[str, Set[str]] = other.get_edges_connections()
        if edge_connections.keys() != other_edge_connections.keys():
            print(f"Missing incoming connections in networks!")
            return False
        # Check connections represented by edges
        for edge_id, incoming_edges in edge_connections.items():
            if edge_id not in other_edge_connections:
                print(f"Missing out-going edge: {edge_id} in connections -> {edge_id, incoming_edges}!")
                return False
            elif other_edge_connections[edge_id] != incoming_edges:
                print(f"Missing connections to edge: {edge_id}, "
                      f"correct: {incoming_edges}, in network: {other_edge_connections}")
                return False
        # Check all keys
        if len(edge_connections.keys() ^ other_edge_connections.keys()) != 0:
            print(f"Network connections are not equal: {edge_connections.keys()} != {other_edge_connections.keys()}")
            return False
        return True

    def __and__(self, other: 'RoadNetwork') -> Optional['RoadNetwork']:
        """
        Performs set intersection on skeleton classes (graphs of road networks), based on objects id's

        :param other: skeleton class, must be loaded from the same network
        :return: New skeleton class, None if error occurred
        """
        return self.intersection(other)

    def __or__(self, other: 'RoadNetwork') -> Optional['RoadNetwork']:
        """
        Performs set union on skeleton classes (graphs of road networks), based on objects id's

        :param other: skeleton class, must be loaded from the same network
        :return: New skeleton class, None if error occurred
        """
        return self.union(other)

    def __xor__(self, other: 'RoadNetwork') -> Optional['RoadNetwork']:
        """
        Performs set difference on skeleton classes (graphs of road networks), based on objects id's

        :param other: skeleton class, must be loaded from the same network
        :return: New skeleton class, None if error occurred
        """
        return self.difference(other)
