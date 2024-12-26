from utc.src.graph.modules.display import GraphModule
from utc.src.graph.network import RoadNetwork, Route, Edge, Junction
from typing import Optional, Union, List, Set


class SubGraph(GraphModule):
    """ Class containing methods which create graphs """

    def __init__(self, road_network: RoadNetwork = None):
        super().__init__(road_network)

    def create_sub_graph(self, components: List[Union[Route, Edge, Junction]]) -> Optional[RoadNetwork]:
        """
        Creates sub-graph from given parts of road network.

        :param components: List of routes/edges/junctions from which sub-graph will be created
        :return: RoadNetwork (sub-graph), None if error occurred
        """
        sub_graph: RoadNetwork = RoadNetwork()
        keep_junctions: Set[str] = set()
        keep_edges: Set[str] = set()
        # -------------------------- Checks and type definitions --------------------------
        if len(components) == 0 or not sub_graph.load(self.road_network):
            return None
        elif all(isinstance(x, Route) for x in components):
            # Add junctions & edges to be kept in graph
            for route in components:
                for edge in route.edge_list:
                    keep_junctions.add(edge.from_junction)
                    keep_junctions.add(edge.to_junction)
                    keep_edges.add(edge.get_id())
        elif all(isinstance(x, Edge) for x in components):
            # Add junctions & edges to be kept in graph
            for edge in components:
                keep_edges.add(edge.get_id())
                keep_junctions.add(edge.from_junction)
                keep_junctions.add(edge.to_junction)
        elif all(isinstance(x, Junction) for x in components):
            # Add junctions to be kept in graph
            keep_junctions = set([junction.get_id() for junction in components])
            # Keep only edges related to given junctions
            keep_edges = set([
                edge.id for edge in self.road_network.edges.values() if
                edge.from_junction in keep_junctions and edge.to_junction in keep_junctions
            ])
        else:  # Incorrect type
            print(f"Expected sub-graph to be given by either list of edges/routes/junctions !")
            return None
        # -------------------------- Cut graph --------------------------
        if (keep_junctions & sub_graph.junctions.keys()) != keep_junctions:
            print(f"Received unknown junction id's: {keep_junctions ^ (keep_junctions & sub_graph.junctions.keys())}")
            return None
        elif (keep_edges & sub_graph.edges.keys()) != keep_edges:
            print(f"Received unknown edge id's: {keep_edges ^ (keep_edges & sub_graph.edges.keys())}")
            return None
        # print(f"Keeping junctions: {keep_junctions}")
        # print(f"Keeping edges: {keep_edges}")
        # Remove junctions
        for junction_id in (sub_graph.junctions.keys() ^ keep_junctions):
            sub_graph.remove_junction(junction_id)
        assert((sub_graph.junctions.keys() & keep_junctions) == keep_junctions)
        assert((sub_graph.edges.keys() & keep_edges) == keep_edges)
        # Remove edges, update edge list, since some could have been removed while removing junctions
        # keep_edges &= sub_graph.edges.keys()
        for edge_id in (sub_graph.edges.keys() ^ keep_edges):
            sub_graph.remove_edge(edge_id)
        assert(sub_graph.edges.keys() == keep_edges)
        sub_graph.edge_connections = sub_graph.get_edges_connections()
        return sub_graph
