from utc.src.constants.static import FilePaths, DirPaths, FileExtension
from utc.src.constants.file_system import XmlFile
from utc.src.graph.network import Graph, RoadNetwork
from typing import Optional, Union, Dict, List, Set
import xml.etree.ElementTree as ET


class FlowEstimator:
    """
    Class estimating flows from vehicle and routes files based on parameters
    """

    def __init__(self, graph: Graph, vehicle_file: Union[str, XmlFile], routes_file: Union[str, XmlFile]):
        """
        :param graph: of the road network
        :param vehicle_file: path or class to vehicle file
        :param routes_file: path or calls to routes file
        """
        self.graph: Graph = graph
        self.vehicle_file: XmlFile = vehicle_file if isinstance(vehicle_file, XmlFile) else XmlFile(vehicle_file)
        self.routes_file: XmlFile = routes_file if isinstance(routes_file, XmlFile) else XmlFile(routes_file)
        assert (self.vehicle_file.is_loaded() and self.routes_file.is_loaded() and self.graph is not None)

    def enumerate_routes(self, route_limit: int = -1) -> Dict[str, int]:
        """
        :param route_limit: number of returned routes, default all
        :return: Sorted dictionary mapping route id to number of vehicles using it
        """
        routes_counts: Dict[str, int] = {route.attrib["id"]: 0 for route in self.routes_file.root.findall("route")}
        for vehicle in self.vehicle_file.root.findall("vehicle"):
            routes_counts[vehicle.attrib["route"]] += 1
        sorted_routes: list = sorted(routes_counts.items(), key=lambda x: x[1], reverse=True)
        route_limit = len(sorted_routes) if route_limit == -1 else route_limit
        return dict(sorted_routes[:route_limit])

    def generate_best_flows(
            self, best_count: int, save_path: str = "",
            generate_subgraph: bool = False
        ) -> Optional[List[ET.Element]]:
        """
        :param best_count: maximum number of flows
        :param save_path: file path where the flows should be saved (optional)
        :param generate_subgraph: True if sub-graphs for flows should be generated, default false
        :return: Generated flows, None if error occurred
        """
        if best_count < 1:
            print(f"Number of best flows must be higher then 0, got: {best_count} !")
            return None
        flows: List[ET.Element] = self.prepare_flows(self.enumerate_routes(best_count), generate_subgraph)
        self.save_flows(flows, save_path)
        return flows

    def generate_dense_flows(self, total_traffic: float, save_path: str = ""):
        """
        :param total_traffic:
        :param save_path: file path where the flows should be saved (optional)
        :return:
        """
        pass

    def prepare_flows(
            self, routes_counts: Dict[str, int],
            generate_subgraph: bool = False
        ) -> Optional[List[ET.Element]]:
        """
        :param routes_counts: list of routes ids
        :param generate_subgraph: True if sub-graphs for flows should be generated, default false
        :return: List of XML Elements containing vehicle flows, None if an error occurred
        """
        if not routes_counts:
            print(f"Received empty mapping of routes, cannot generate flows!")
            return None
        # Use dict to keep flows sorted by highest count
        ret_val: Dict[str, ET.Element] = {key: None for key in routes_counts.keys()}
        for vehicle_route in self.routes_file.get_elements("route", set(routes_counts.keys())):
            edges: List[str] = vehicle_route.attrib["edges"].split()
            first_edge: str = edges[0]
            last_edge: str = edges[-1]
            # Check
            if not self.graph.road_network.edge_exists(first_edge):
                return None
            elif not self.graph.road_network.edge_exists(last_edge):
                return None
            from_junction: str = self.graph.road_network.get_edge(first_edge).from_junction
            to_junction: str = self.graph.road_network.get_edge(last_edge).to_junction
            edges: Set[str] = set()
            if generate_subgraph:
                routes = self.graph.path_finder.top_k_a_star(from_junction, to_junction, 1.3)
                if routes is None:
                    return None
                for route in routes:
                    edges |= set(route.get_edge_ids(False))
            # Generate XML flow
            ret_val[vehicle_route.attrib["id"]] = ET.Element("flow", {
               "id": vehicle_route.attrib["id"],
               "fromJunction": from_junction,
               "toJunction": to_junction,
               "edges": "" if not edges else " ".join(edges),
               "numVehicles": str(routes_counts[vehicle_route.attrib["id"]])
            })
        return list(ret_val.values())

    def save_flows(self, flows: List[ET.Element], save_path: str) -> bool:
        """
        :param flows:
        :param save_path:
        :return: True on success, false otherwise
        """
        if not save_path:
            print(f"Invalid save path, empty string!")
            return False
        flow_file: XmlFile = XmlFile(FilePaths.VEHICLE_FLOWS_TEMPLATE)
        for flow in flows:
            flow_file.root.append(flow)
        print(f"Sa")
        return flow_file.save(save_path)


# For testing purposes
if __name__ == "__main__":
    scenario_name: str = "itsc_25200_28800_filtered"
    vehicle_file: str = FilePaths.SCENARIO_VEHICLES.format(scenario_name, scenario_name)
    routes_file: str = FilePaths.SCENARIO_ROUTES.format(scenario_name, scenario_name)
    flow_file: str = FilePaths.SCENARIO_FLOWS.format(scenario_name, scenario_name)
    graph: Graph = Graph(RoadNetwork())
    graph.loader.load_map(FilePaths.MAP_SUMO.format("DCC_subgraph_red"))
    flow_estimator: FlowEstimator = FlowEstimator(graph, vehicle_file, routes_file)
    flow_estimator.generate_best_flows(4, flow_file, True)














