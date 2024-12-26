from utc.src.graph.modules.graph_module import GraphModule
from utc.src.graph.network import RoadNetwork
from typing import Set


class Control(GraphModule):
    """ Class providing utility methods to test graph correctness """

    def __init__(self, road_network: RoadNetwork):
        super().__init__(road_network)

    def check_graph(self) -> bool:
        """
        :return: True if graph has all its components connected, no empty junctions, etc.
        Warning or Error message will be written otherwise.
        """
        return self.check_edges() and self.check_junctions() and self.check_routes()

    def check_edges(self) -> bool:
        """
        :return: Checks all edges for validity, their connected junctions existence etc.
        """
        if len(self.road_network.edges) == 0:
            print(f"Error, edges of road network is an empty mapping!")
            return False
        used_junctions: Set[str] = set()
        for edge_id, edge in self.road_network.edges.items():
            if not edge.attributes:
                return False
            elif not self.road_network.junction_exists(edge.from_junction):
                return False
            elif not self.road_network.junction_exists(edge.to_junction):
                return False
            used_junctions |= {edge.from_junction, edge.to_junction}
        # Check connections
        if len(used_junctions ^ self.road_network.junctions.keys()) != 0:
            print(f"Warning found missing or unused junctions: {used_junctions ^ self.road_network.junctions.keys()}!")
            return False
        return True

    def check_junctions(self) -> bool:
        """
        :return: Checks all junctions for validity, their routes etc.
        """
        if len(self.road_network.junctions) == 0:
            print(f"Error, junctions of road network is an empty mapping!")
            return False
        used_routes: Set[str] = set()
        for junction_id, junction in self.road_network.junctions.items():
            if not junction.connections:
                return False
            elif junction.is_starting() and junction_id not in self.road_network.starting_junctions:
                print(f"Junction: {junction_id} is starting, but not in starting mapping!")
                return False
            elif junction.is_ending() and junction_id not in self.road_network.ending_junctions:
                print(f"Junction: {junction_id} is ending, but not in ending mapping!")
                return False
            used_routes |= set([route.id for route in junction.get_routes()])
        # Check connections
        if len(used_routes ^ self.road_network.routes.keys()) != 0:
            print(f"Warning found missing or unused routes: {used_routes ^ self.road_network.routes.keys()}!")
            return False
        return True

    def check_routes(self) -> bool:
        """
        :return: Checks all edges for validity, their connected junctions existence etc.
        """
        if len(self.road_network.routes) == 0:
            print(f"Error, routes of road network is an empty mapping!")
            return False
        used_edges: Set[str] = set()
        for route_id, route in self.road_network.routes.items():
            if not route.is_valid():
                return False
            elif not self.road_network.junction_exists(route.get_start()):
                print(f"Starting junction: {route.get_start()} of route: {route_id}, does not exists!")
                return False
            elif not self.road_network.junction_exists(route.get_destination()):
                print(f"Ending junction: {route.get_destination()} of route: {route_id}, does not exists!")
                return False
            used_edges |= set(route.get_edge_ids(False))
        # Check connections
        if len(used_edges ^ self.road_network.edges.keys()) != 0:
            print(f"Warning found missing or unused edges: {used_edges ^ self.road_network.edges.keys()}!")
            return False
        return True

    def check_connections(self, original: RoadNetwork) -> bool:
        """
        :return: Checks if junctions are truly as connected as they should be compared to original graph
        """
        if original is None:
            print(f"Original network is of type 'None' !")
            return False
        connections = self.road_network.get_edges_connections()
        original_connections = original.get_edges_connections()
        if not (connections.keys() & original_connections.keys()):
            print(f"Graphs do not share edges!")
            return False
        for destination_edge, incoming_edges in connections.items():
            if destination_edge not in original_connections:
                print(f"Invalid destination edge: {destination_edge}!")
                return False
            elif (incoming_edges & original_connections[destination_edge]) != (self.road_network.edges.keys() & original_connections[destination_edge]):
                print(f"Missing incoming edges to edge: {destination_edge}, got: {incoming_edges}, expected: {self.road_network.edges.keys() & original_connections[destination_edge]}")
                return False
        return True


