from utc.src.graph.network import RoadNetwork


class GraphModule:
    """ Super class for classes which work with road networks """

    def __init__(self, road_network: RoadNetwork):
        """
        :param road_network: of graph (default None)
        :raises TypeError if parameter 'road_network' is None or not instance of RoadNetwork class
        """
        if road_network is None or not isinstance(road_network, RoadNetwork):
            raise TypeError(f"Argument 'road_network' has to be of type 'RoadNetwork', got: '{type(road_network)}'!")
        self.road_network: RoadNetwork = road_network

    def set_network(self, road_network: RoadNetwork) -> None:
        """
        Setter for graph, has to be called for each
        child class before using their methods

        :param road_network: of graph
        :return: None
        :raises TypeError if parameter 'road_network' is None or not instance of RoadNetwork class
        """
        if road_network is None or not isinstance(road_network, RoadNetwork):
            raise TypeError(f"Argument 'road_network' has to be of type 'RoadNetwork', got: '{type(road_network)}'!")
        self.road_network = road_network
