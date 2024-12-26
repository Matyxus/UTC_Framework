from utc.src.routing.pddl.pddl_episode import PddlEpisode
from utc.src.routing.pddl.base.pddl_vehicle import PddlVehicle
from utc.src.graph import Edge, RoadNetwork, Graph
from typing import Optional, Dict, List, Set
from xml.etree.ElementTree import Element


class Parser:
    """
    Class parsing pddl result files and converting them back to vehicle's routes
    """
    def __init__(self, graph: Graph, sub_graph: Optional[Graph] = None):
        """
        :param graph: used to route vehicles on
        :param sub_graph: optional argument for when vehicles are routed in sub-graph
        """
        self.graph: Graph = graph
        self.sub_graph: Optional[Graph] = sub_graph

    def process_result(self, episode: PddlEpisode) -> Optional[Dict[Element, Element]]:
        """
        :param episode: pddl episode
        :return: Mapping of vehicle paired with new routes in XML format
        """
        # print(f"Processing episode: {episode.id}")
        # Check episode
        if episode is None or episode.problem is None:
            raise ValueError("Error, received invalid episode!")
        elif not episode.is_valid():
            print("Unable to process episode, no results were generated, returning default paths")
            return {
                vehicle.vehicle.to_xml(): vehicle.original_route
                for vehicle in episode.problem.container.vehicles.values()
            }
        # Parse result
        new_paths: Dict[Element, Element] = {}
        routed: Set[str] = set()
        for vehicle_id, pddl_routes in episode.result.parse_result().items():
            vehicle: PddlVehicle = episode.problem.container.get_vehicle(vehicle_id)
            routed.add(vehicle.vehicle.id)
            assert(vehicle is not None)
            # Get new vehicle route
            route: Optional[Element] = self.create_route(vehicle, pddl_routes, episode.problem.network)
            if route is None:
                print(f"No new route found for vehicle: '{vehicle_id}', using default")
                new_paths[vehicle.vehicle.to_xml()] = vehicle.original_route
                continue
            new_paths[vehicle.vehicle.to_xml()] = route
        episode.problem.container.info.routed = len(routed)
        # Fill the rest with vehicles default paths
        for vehicle_id in (episode.problem.container.vehicles.keys() ^ routed):
            assert(vehicle_id not in routed)
            vehicle: PddlVehicle = episode.problem.container.vehicles[vehicle_id]
            new_paths[vehicle.vehicle.to_xml()] = vehicle.original_route
        return new_paths

    # -------------------------------- Utils --------------------------------

    def create_route(self, vehicle: PddlVehicle, pddl_routes: List[int], network: RoadNetwork) -> Optional[Element]:
        """
        :param vehicle: pddl vehicle
        :param pddl_routes: list of route id's (internal) extracted from pddl result
        :param network: network on which vehicle was routed
        :return: New route of vehicle as XML element, None if error occurred
        """
        # Create edge sequence of original id's
        edges: List[str] = []
        for route in network.get_routes(pddl_routes):
            assert(route is not None)
            edges.extend(route.get_edge_ids(internal=False))
        # Make sure vehicle entered and exited graph by the same junction
        assert(vehicle.graph_route.first_edge().from_junction == network.get_edge(edges[0]).from_junction)
        assert(vehicle.graph_route.last_edge().to_junction == network.get_edge(edges[-1]).to_junction)
        original_edges: List[str] = vehicle.original_route.attrib["edges"].split()
        previous_edges: List[Edge] = self.graph.road_network.get_edges((original_edges[0], original_edges[-1]))
        # Insert path into original path, only when we have sub-path
        if vehicle.indexes != (0, -1):
            # Graph route must be sub-route of original
            assert(" ".join(vehicle.graph_route.get_edge_ids()) in vehicle.original_route.attrib["edges"])
            original_edges[vehicle.indexes[0]:vehicle.indexes[-1]] = edges
        else:
            original_edges = edges
        # Check new route
        if not self.graph.road_network.check_edge_sequence(original_edges):
            print(f"Error in route construction for vehicle: '{vehicle.pddl_id}'")
            return None
        # Make sure that the new route begins and ends in the same junction as original
        new_edges: List[Edge] = self.graph.road_network.get_edges((original_edges[0], original_edges[-1]))
        assert(previous_edges[0].from_junction == new_edges[0].from_junction)
        assert(previous_edges[1].to_junction == new_edges[1].to_junction)
        return Element("route", {"id": "unknown", "edges": " ".join(original_edges)})
