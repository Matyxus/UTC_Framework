from utc.src.routing.pddl.base.vehicle_container import PddlVehicle, VehicleContainer, VehicleInfo
from utc.src.routing.pddl.pddl_options import NetworkOptions
from utc.src.routing.traffic.cache import Cache
from utc.src.graph import Graph, RoadNetwork, Route, Junction
from utc.src.clustering.similarity.similarity_clustering import SimilarityClustering
from typing import Optional, List, Dict, Set, FrozenSet
from copy import deepcopy


class NetworkBuilder:
    """
    Class building road networks for pddl problem files
    """
    def __init__(self, graph: Graph, sub_graph: Graph, options: NetworkOptions):
        """
        :param graph: on which vehicles are driving
        :param sub_graph: optional parameter (sub-graph of the original network),
        will be used for planning vehicles routes
        """
        assert(None not in (graph, sub_graph, options))
        self.graph: Graph = graph
        self.sub_graph: Graph = sub_graph
        self.options: NetworkOptions = options
        self.allowed_edges: Dict[str, Set[str]] = self.prepare_graph(graph, sub_graph)
        self.sim_clustering: SimilarityClustering = SimilarityClustering(options.dbscan)
        # Memory of previously constructed sub-graphs
        self.cache: Cache = Cache()

    # ------------------------------------------ Network construction ------------------------------------------

    def build_network(self, container: VehicleContainer) -> Optional[RoadNetwork]:
        """
        :param container: of vehicles
        :return: RoadNetwork (Sub-network) build for vehicles with each subgraph forming it,
        can be empty if network was not build
        """
        assert(container is not None)
        return self.combine_parts(self.build_parts(container))

    def combine_parts(self, edges: Set[int]) -> Optional[RoadNetwork]:
        """
        :param edges: which will form the road_network
        :return: Road network build from combining all subgraph's, None if error occurred
        """
        if edges is None or not edges:
            return None
        return self.sub_graph.sub_graph.create_sub_graph(self.sub_graph.road_network.get_edges(edges))

    def build_parts(self, container: VehicleContainer) -> Optional[Set[int]]:
        """
        :param container: of vehicles
        :return: True on success, false otherwise
        """
        print(f"Building sub-graphs for {len(container.vehicles)} vehicles")
        # Checks
        if not container.vehicles:
            print("Invalid vehicles, mapping is empty, cannot construct subgraph!")
            return None
        edges: Set[int] = set()
        count: int = 0
        # For all vehicle generate corresponding sub-graph (all found edges)
        for pddl_vehicle in container.vehicles.values():
            pddl_vehicle.sub_graph = self.generate_routes(pddl_vehicle, container.info)
            if pddl_vehicle.sub_graph is not None:
                edges |= pddl_vehicle.sub_graph
                count += 1
        print(f"Found: {count} sub-graphs")
        return edges

    # ------------------------------------------ Route generation ------------------------------------------

    def generate_routes(self, pddl_vehicle: PddlVehicle, info: VehicleInfo) -> Optional[FrozenSet[int]]:
        """
        :param pddl_vehicle: class holding attributes of vehicle
        :param info: information about vehicles
        :return: List of found routes, None if this route was already explored
        """
        # print(f"------ Routing vehicle: {pddl_vehicle.vehicle.get_attribute('id')} ------")
        # Generate route for vehicle on graph
        original_edges: List[str] = pddl_vehicle.original_route.attrib["edges"].split()
        edges, indexes = self.sub_graph.road_network.get_longest_sequence(original_edges)
        if not edges:
            info.invalid_route += 1
            # print(f"Vehicle: {pddl_vehicle.vehicle.attributes['id']} does not drive on network !")
            return None
        elif len(edges) < 3:
            info.short_route += 1
            # print(f"Route: {pddl_vehicle.graph_route} has too short path, will only count it")
            return None
        pddl_vehicle.set_graph_route(Route(edges), indexes)
        assert (all([self.sub_graph.road_network.edge_exists(edge) for edge in edges]))
        assert (None not in self.graph.road_network.get_edges(edges))
        assert (original_edges[indexes[0]:indexes[1]] == pddl_vehicle.graph_route.get_edge_ids())
        assert (original_edges[indexes[0]] == pddl_vehicle.graph_route.first_edge().id)
        assert (original_edges[indexes[1]-1] == pddl_vehicle.graph_route.last_edge().id)
        # Extract initial and ending junctions of route
        start_junction: Junction = self.sub_graph.road_network.get_junction(pddl_vehicle.graph_route.get_start())
        end_junction: Junction = self.sub_graph.road_network.get_junction(pddl_vehicle.graph_route.get_destination())
        # Find which out-going routes from first junction we cannot use, if its not first edge
        if (indexes[0]-1) > 0 and self.allowed_edges:
            incoming_edge: str = original_edges[indexes[0] - 1]
            # print(f"Incoming edge: {incoming_edge}")
            for out_route in start_junction.get_out_routes():
                out_route.allowed_first = False
                if out_route.last_edge().id not in self.allowed_edges:
                    continue
                # Find edges, which are out_going from the incoming edge to subgraph
                elif incoming_edge in self.allowed_edges[out_route.last_edge().id]:
                    out_route.allowed_first = True
                    # print(f"Route: {out_route} is allowed!")
        else:  # Make sure vehicle starts at the current edge
            for out_route in start_junction.get_out_routes():
                out_route.allowed_first = (out_route.first_edge().id == original_edges[indexes[0]])
        # Find out which in-coming routes from last junction we cannot use
        if indexes[1] < len(original_edges) and self.allowed_edges:
            allowed_out_edges: Set[str] = self.allowed_edges.get(original_edges[indexes[1]])
            assert(len(allowed_out_edges) != 0)
            for in_route in end_junction.get_in_routes():
                in_route.allowed_last = (in_route.last_edge().id in allowed_out_edges)
        else:  # Make sure vehicle goes into last junction in such a way, that it has same options as originally
            for in_route in end_junction.get_in_routes():
                in_route.allowed_last = (in_route.last_edge().id == original_edges[-1])
        # Allowed Starting and ending routes of vehicle (filter out duplicates)
        pddl_vehicle.allowed_starting = tuple(set([
            out_route.get_id(True) for out_route in start_junction.get_out_routes() if out_route.allowed_first
        ]))
        pddl_vehicle.allowed_ending = tuple([
            in_route.get_id(True) for in_route in end_junction.get_in_routes() if in_route.allowed_last
        ])
        # print(pddl_vehicle.allowed_starting)
        # print(pddl_vehicle.allowed_ending)
        assert(len(pddl_vehicle.allowed_ending) != 0)
        assert(len(pddl_vehicle.allowed_starting) != 0)
        assert(len(set(pddl_vehicle.allowed_ending)) == len(pddl_vehicle.allowed_ending))
        # Check if we already generated such sub-graph, if yes return it (can be also 'None')
        if self.cache.has_mapping(pddl_vehicle.allowed_starting, pddl_vehicle.allowed_ending):
            # print(f"Mapping for vehicle exists ...")
            return self.cache.get_mapping(pddl_vehicle.allowed_starting, pddl_vehicle.allowed_ending)
        routes: List[Route] = self.sub_graph.path_finder.top_k_a_star(
            start_junction.id, end_junction.id,
            c=self.options.topka.c, k=self.options.topka.k
        )
        # Reset allowed on routes
        for out_route in start_junction.get_out_routes():
            out_route.allowed_first = True
        for in_route in end_junction.get_in_routes():
            in_route.allowed_last = True
        # Invalid routes, or only shortest path was found
        if routes is None or not routes or len(routes) == 1:
            # print(f"Error unable to find routes for vehicle: {pddl_vehicle.vehicle.attributes['id']}!")
            info.invalid_route += 1
            self.cache.invalid.add((pddl_vehicle.allowed_starting, pddl_vehicle.allowed_ending))
            return None
        # For all routes check, that they form valid sequence if inserted back to original
        for found_route in routes:
            tmp = deepcopy(original_edges)
            tmp[indexes[0]:indexes[1]] = found_route.get_edge_ids()
            # print(f"Found route: {found_route}")
            assert(self.graph.road_network.check_edge_sequence(tmp))
        # Apply clustering on routes
        indexes: Optional[List[int]] = self.sim_clustering.calculate(routes)
        if indexes is not None and indexes:
            # print(f"Applied DBSCAN on routes ...")
            routes = [routes[index] for index in indexes]
        return self.cache.save_mapping(pddl_vehicle.allowed_starting, pddl_vehicle.allowed_ending, routes)

    # ---------------------------------------- Utils ----------------------------------------

    def prepare_graph(self, graph: Graph, sub_graph: Graph) -> Dict[str, Set[str]]:
        """
        :param graph: original graph
        :param sub_graph: of original graph
        :return: Mapping of incoming edges to sub-graph from original graph
        """
        print(f"Preparing sub-graph connections to original graph ...")
        # Find junctions on original graph, which are neighbours to sub-graph
        neighbours: Set[str] = set()
        sub_junctions = sub_graph.road_network.junctions
        for edge in graph.road_network.edges.values():
            if edge.id in sub_graph.road_network.edges:
                continue
            if edge.from_junction in sub_junctions:
                neighbours.add(edge.from_junction)
            if edge.to_junction in sub_junctions:
                neighbours.add(edge.to_junction)
        return graph.road_network.get_edges_connections(neighbours)

