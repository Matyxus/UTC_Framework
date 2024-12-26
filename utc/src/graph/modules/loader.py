from utc.src.constants.static.graph_attributes import EdgeAttributes, NodeAttributes, filter_attributes
from utc.src.constants.file_system.file_types.sumo_network_file import SumoNetworkFile
from utc.src.graph.modules.graph_module import GraphModule
from utc.src.graph.network import RoadNetwork, Junction, Edge, Route
from typing import Dict, List, Set, Optional


class Loader(GraphModule):
    """ Loads graph from SUMO's network ('.net.xml') file """

    def __init__(self, road_network: RoadNetwork):
        super().__init__(road_network)
        self.network_file: Optional[SumoNetworkFile] = None

    def load_map(self, network_path: str) -> bool:
        """
        :param network_path: path to network file (default is utc/data/maps/sumo)
        :return: true on success, false otherwise
        """
        # print(f"Loading network: '{network_path}'")
        self.network_file = SumoNetworkFile(network_path)
        if not self.network_file.is_loaded():  # File does not exist
            return False
        elif not self.load_junctions():
            print("Error while loading junctions!")
            return False
        elif not self.load_edges():
            print("Error while loading edges!")
            return False
        elif not self.load_connections():  # Error in connections (missing Junction / Edge id, ..)
            return False
        self.road_network.roundabouts = self.load_roundabouts()
        self.road_network.map_name = self.network_file.get_name()
        # print("Finished loading road network")
        # return True
        return self.check_status()

    def load_junctions(self) -> bool:
        """
        Loads junctions from network ('.net.xml') file, must be called first!

        :return: True on success, false otherwise
        """
        # print("Loading & creating junctions")
        for index, xml_junction in enumerate(self.network_file.get_junctions()):
            attributes: dict = filter_attributes(xml_junction.attrib, NodeAttributes.JUNCTION_ATTRIBUTES)
            if not self.road_network.add_junction(Junction(attributes, index)):
                return False
        # print("Finished loading & creating junctions")
        return len(self.road_network.junctions) != 0

    def load_edges(self) -> bool:
        """
        Loads edges from network ('.net.xml') file, must be called after loading junctions!

        :return: True on success, false otherwise
        """
        # print("Loading & creating edges, routes")
        for index, xml_edge in enumerate(self.network_file.get_edges()):
            attributes: dict = filter_attributes(xml_edge.attrib, EdgeAttributes.EDGE_ATTRIBUTES)
            lane_attributes: dict = {}
            for lane in xml_edge.findall("lane"):
                lane_attributes[lane.attrib["id"]] = filter_attributes(lane.attrib, EdgeAttributes.LANE_ATTRIBUTES)
            edge: Edge = Edge(attributes, lane_attributes, index)
            if not self.road_network.add_edge(edge):
                return False
            elif not self.road_network.add_route(Route(edge, f"r{index}", index)):
                return False
        # print("Finished loading & creating edges, routes")
        return len(self.road_network.edges) != 0

    def load_connections(self, self_loops: bool = False) -> bool:
        """
        Loads connections from network ('.net.xml') file, assigns routes to junctions,
        identifies starting/ending junctions, must be called after loading edges & junctions!

        :param self_loops: True if loops on fringe junctions should be allowed, False by default
        :return: True on success, false otherwise
        """
        # print("Loading & creating connections between junctions")
        # ----------------- Connections -----------------
        connections: Dict[str, Set[str]] = {
            # to_edge_id: {from_edge_id, ..}, ..
        }
        for connection in self.network_file.get_connections():
            if connection.attrib["to"] not in connections:
                connections[connection.attrib["to"]] = set()
            connections[connection.attrib["to"]].add(connection.attrib["from"])
            # Check existence
            for edge_id in [connection.attrib["to"], connection.attrib["from"]]:
                if not self.road_network.edge_exists(edge_id):
                    print(f"Invalid connection edge: '{edge_id}', corresponding edge does not exist!")
                    return False
        # print(connections)
        # Disable turnarounds (u-turns) on junctions
        # for edge_id in list(connections.keys()):
        #     for neigh_edge in list(connections[edge_id]):
        #         if neigh_edge not in connections:
        #             continue
        #         elif edge_id in connections[neigh_edge]:
        #             connections[edge_id] -= {neigh_edge}
        #             connections[neigh_edge] -= {edge_id}

        # ------------------- Assign routes, to junctions -------------------
        for route in self.road_network.routes.values():
            # Routes only have 1 edge each
            edge_id: str = route.first_edge().get_id()
            from_junction: Junction = self.road_network.get_junction(route.get_start())
            to_junction: Junction = self.road_network.get_junction(route.get_destination())
            to_junction.add_connection(route, None)
            if edge_id in connections:
                # Check if we allow self loops
                if not self_loops and len(connections[edge_id]) == 1 and \
                        self.is_loop(edge_id, next(iter(connections[edge_id]))):
                    # print(f"Found loop at junction: {self.road_network.edges[edge_id].from_junction}, changing route!")
                    from_junction.add_connection(None, route)
                else:
                    for in_edge_id in connections[edge_id]:
                        # Map internal edge id into route (when network is not modified, mapping is 1:1),
                        # meaning, internal id of edge corresponds to route that represents this edge
                        from_junction.add_connection(
                            self.road_network.get_route(self.road_network.edges[in_edge_id].get_id(internal=True)),
                            route
                        )
            else:  # No connection to this edge, from_junction is fringe (starting)
                from_junction.add_connection(None, route)
                # print(f"Junction: {from_junction.get_id(False)} is starting !")
        # ------------------- Starting & ending junctions -----------------
        # Find nodes, which have only 1 in_route and 1 out_route,
        # if in_route_start is equal to out_route_destination, remove it
        for junction in self.road_network.junctions.values():
            in_routes: List[Route] = junction.get_in_routes()
            out_routes: List[Route] = junction.get_out_routes()
            if len(in_routes) == len(out_routes) == 1:
                in_route: Route = in_routes[0]
                out_route: Route = out_routes[0]
                # Remove self loops on fringe junctions
                if not self_loops and junction.connection_exists(in_route, out_route, False) and \
                        in_route.get_start() == out_route.get_destination():
                    # Change self loop, incoming route will be 'None'
                    raise ValueError("Found loop, should have been removed before!")
                    # junction.remove_connection(in_route, out_route)
                    # junction.add_connection(None, out_route)
            # Check junctions if they are on fringe
            self.road_network.check_fringe(junction)
        # print("Finished loading & creating edges, connections")
        return True

    def load_roundabouts(self) -> List[List[str]]:
        """
        :return: List of roundabouts (each roundabout is list of junctions ids forming it)
        """
        roundabouts: list = []
        for xml_roundabout in self.network_file.get_roundabouts():
            roundabout: List[str] = xml_roundabout.attrib["nodes"].split()
            # Check for correctness (this is important when loading sub-graphs)
            if self.check_roundabout(roundabout):
                roundabouts.append(roundabout)
        return roundabouts

    # ----------------------------------- Utils -----------------------------------

    def check_status(self) -> bool:
        """
        :return: True if network was loaded correctly, False otherwise
        """
        if self.network_file is None:
            print(f"Expected network file!")
            return False
        # print(f"Checking if network connections were build correctly ...")
        # 1st check that all junctions & edges were loaded
        for xml_junction in self.network_file.get_junctions():
            if xml_junction.attrib["id"] not in self.road_network.junctions:
                return False
        for xml_edge in self.network_file.get_edges():
            if xml_edge.attrib["id"] not in self.road_network.edges:
                return False
        # 2nd check that connections represented by junctions correspond to what is in file
        connections: Dict[str, Set[str]] = {
            # to_edge_id: {from_edge_id, ..}, ..
        }
        for connection in self.network_file.get_connections():
            if connection.attrib["to"] not in connections:
                connections[connection.attrib["to"]] = set()
            connections[connection.attrib["to"]].add(connection.attrib["from"])
        # Filter out self-loops
        for edge_id in list(connections.keys()):
            if len(connections[edge_id]) != 1:
                continue
            if self.is_loop(edge_id, next(iter(connections[edge_id]))):
                # print(f"Found loop at junction: {self.road_network.edges[edge_id].from_junction}")
                connections.pop(edge_id)
        network_connections: Dict[str, Set[str]] = self.road_network.get_edges_connections()
        # print(connections)
        # print(network_connections)
        for edge_id, incoming_edges in connections.items():
            if edge_id not in network_connections:
                print(f"Missing out-going edge: {edge_id} in connections -> {edge_id, incoming_edges}!")
                return False
            elif network_connections[edge_id] != incoming_edges:
                print(f"Missing connections to edge: {edge_id}, "
                      f"correct: {incoming_edges}, in network: {network_connections}")
                return False
        # Check all keys
        if len(connections.keys() ^ network_connections.keys()) != 0:
            print(f"Network connections has more edges -> {connections.keys()} != {network_connections.keys()}")
            return False
        self.network_file = None  # Clear
        self.road_network.edge_connections = network_connections
        # print(f"Network connections are correct")
        return True

    def check_roundabout(self, roundabout: List[str]) -> bool:
        """
        :param roundabout: list of junction id's forming roundabout (called after whole graph is loaded)
        :return: True if roundabout is truly a roundabout, False otherwise
        """
        if not len(roundabout):  # Empty roundabout
            print(f"Received empty list of junctions for roundabout!")
            return False
        # Prepare dictionary mapping if the roundabout junction was visited
        visited: Dict[str, bool] = {junction_id: False for junction_id in roundabout}
        # For every junction, check if it is connected to another roundabout junction
        # Roundabout list does not have to be sorted, since we have to go in circle no matter where we start
        for junction_id in roundabout:
            junction: Junction = self.road_network.get_junction(junction_id)
            # Check existence
            if junction is None:
                print(f"Roundabout: '{roundabout}' junction: '{junction_id}' does not exist!")
                return False
            roundabout_neighbour: Set[str] = junction.get_out_neighbours() & visited.keys()
            # Check connection
            if not roundabout_neighbour:
                print(f"Roundabout: '{roundabout}' junction: '{junction_id}' does not connect to any other!")
                return False
            elif len(roundabout_neighbour) > 1:
                print(f"Roundabout: '{roundabout}' junction: '{junction_id}' "
                      f"connects to multiple roundabout junctions: '{roundabout_neighbour}' !")
                return False
            neighbour_id: str = roundabout_neighbour.pop()
            if visited[neighbour_id]:
                print(f"Roundabout: '{roundabout}' connections are incorrect, "
                      f"junction: '{neighbour_id}' was already visited")
                return False
            visited[neighbour_id] = True
        # Roundabout is only correct, if we visited all its junctions
        if not all(visited.values()):
            print(f"Roundabout: '{roundabout}' doest not have correct connections, "
                  f"not all junction were visited: '{visited}' !")
        return True

    def is_loop(self, to_edge: str, from_edge: str) -> bool:
        """
        :param to_edge:
        :param from_edge:
        :return:
        """
        to_edge: Edge = self.road_network.get_edge(to_edge)
        from_edge: Edge = self.road_network.get_edge(from_edge)
        if to_edge is None or from_edge is None:
            raise ValueError("")
        return to_edge.from_junction == from_edge.to_junction and to_edge.to_junction == from_edge.from_junction
