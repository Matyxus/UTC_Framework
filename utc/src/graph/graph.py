from utc.src.graph.network import RoadNetwork
from utc.src.graph.modules import GraphModule, Loader, Simplify, PathFinder, Display, SubGraph, Control


class Graph(GraphModule):
    """ Class holding road network of graph and all graph modules (subclass of GraphModule) """

    def __init__(self, road_network: RoadNetwork):
        super(Graph, self).__init__(road_network)
        self.loader: Loader = Loader(self.road_network)
        self.simplify: Simplify = Simplify(self.road_network)
        self.path_finder: PathFinder = PathFinder(self.road_network)
        self.display: Display = Display(self.road_network)
        self.sub_graph: SubGraph = SubGraph(self.road_network)
        self.control: Control = Control(self.road_network)

    def set_network(self, road_network: RoadNetwork) -> None:
        """
        :param road_network: to be set for graph modules (and graph itself)
        :return: None
        """
        super().set_network(road_network)
        self.loader.set_network(self.road_network)
        self.simplify.set_network(self.road_network)
        self.path_finder.set_network(self.road_network)
        self.display.set_network(self.road_network)
        self.sub_graph.set_network(self.road_network)
        self.control.set_network(self.road_network)


# # For testing purposes
if __name__ == '__main__':
    import time
    from utc.src.constants.dynamic.my_logging import initialize_logger
    from utc.src.constants.static import FilePaths
    from utc.src.constants.file_system.file_types.xml_file import XmlFile
    initialize_logger()
    network_name: str = "13_06_58_sydney_increasing_default_sg"
    graph: Graph = Graph(RoadNetwork())
    graph.loader.load_map(network_name)
    print(f"Network has: {len(graph.road_network.junctions)} junctions")
    print(f"Network has: {len(graph.road_network.edges)} edges")
    print(f"Network has: {len(graph.road_network.routes)} routes")
    print(graph.road_network.get_edge("5").internal_id)
    print(graph.road_network.get_junction("77"))
    # print(graph.)










