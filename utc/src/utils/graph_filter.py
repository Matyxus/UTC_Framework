from utc.src.graph import Graph, RoadNetwork
from utc.src.simulator.scenario import Scenario
from utc.src.utils.vehicle_extractor import VehicleExtractor, VehicleEntry
from xml.etree.ElementTree import Element
from typing import Set, Dict, List


class GraphFilter:
    """
    Class filtering scenarios onto a given subgraph creating new scenario in the process.
    Usually the suffix '_filtered' is added to such scenarios names (unless custom option is chosen).
    """
    def __init__(self, min_edges: int = 3):
        """
        :param min_edges: minimal amount of edges for routes (as sequence)
        """
        self.min_edges = min_edges

    def filter_scenario(
            self, scenario_name: str, road_network: str,
            new_scenario_name: str = "default", full_path: bool = True
        ) -> bool:
        """
        :param scenario_name: name of scenario folder we want to transform
        :param road_network: name of road network on which we want to focus traffic
        :param new_scenario_name: name of newly generated scenario (per default suffix '_filtered' is added to original)
        :param full_path: True if full path of vehicle should be in new simulation or only path on given network
        :return: True on success, false otherwise
        """
        # Checks
        original_scenario: Scenario = Scenario(scenario_name)
        graph: Graph = Graph(RoadNetwork())
        if not original_scenario.exists():
            print(f"Scenario: {scenario_name} does not exist!")
            return False
        elif not graph.loader.load_map(road_network):
            print(f"Unable to load network: {road_network}!")
            return False
        new_scenario_name = (scenario_name + "_filtered") if new_scenario_name == "default" else new_scenario_name
        # Initialize new scenario
        new_scenario: Scenario = Scenario(new_scenario_name, True)
        routes_mapping: Dict[str, str] = {}
        for original_route in original_scenario.routes_file.root.findall("route"):
            sequence, indexes = graph.road_network.get_longest_sequence(original_route.attrib["edges"].split())
            # Unable to find at any common edges with subgraph, this vehicle does not travel on subgraph
            if not sequence:
                continue
            elif full_path:
                routes_mapping[original_route.attrib["id"]] = new_scenario.routes_file.add_route(Element("route", {
                    "id": original_route.attrib["id"],
                    "edges": original_route.attrib["edges"],
                }))
                continue
            # Save new route with new edges, along with new id of route
            routes_mapping[original_route.attrib["id"]] = new_scenario.routes_file.add_route(Element("route", {
                "id": original_route.attrib["id"],
                "edges": " ".join([edge.id for edge in sequence]),
            }))
        # Change vehicles routes
        for original_vehicle in original_scenario.vehicles_file.root.findall("vehicle"):
            if original_vehicle.attrib["route"] in routes_mapping:
                original_vehicle.attrib["route"] = routes_mapping[original_vehicle.attrib["route"]]
                new_scenario.vehicles_file.add_vehicle(original_vehicle)
        return new_scenario.save(original_scenario.config_file.get_network())

    def filter_planned(self, original: str, planned: str, road_network: str) -> bool:
        """
        :param original:
        :param planned:
        :param road_network:
        :return:
        """
        # Checks
        original_scenario: Scenario = Scenario(original)
        planned_scenario: Scenario = Scenario(planned)
        graph: Graph = Graph(RoadNetwork())
        if not original_scenario.exists() or not planned_scenario.exists():
            return False
        elif not graph.loader.load_map(road_network):
            print(f"Unable to load network: {road_network}!")
            return False
        # Initialize new scenario
        new_scenario: Scenario = Scenario(planned + "_filtered", True)
        entry: VehicleEntry = VehicleExtractor(
            original_scenario.vehicles_file, original_scenario.routes_file
        ).estimate_arrival_naive((25200, 32400))
        entry2: VehicleEntry = VehicleExtractor(
            planned_scenario.vehicles_file, planned_scenario.routes_file
        ).estimate_arrival_naive((25200, 32400))
        for vehicle in entry.vehicles.values():
            vehicle_id: str = vehicle.attributes["id"]
            assert (vehicle_id in entry2.vehicles)
            route = entry.original_routes[vehicle.attributes["route"]]
            route_edges = graph.road_network.get_edges(route.attrib["edges"].split())
            assert(None not in route_edges)
            route2 = entry2.original_routes[entry2.vehicles[vehicle_id].attributes["route"]]
            route2_edges = route2.attrib["edges"].split()
            seq2, indexes2 = graph.road_network.get_longest_sequence(route2_edges)
            assert(seq2 is not None and len(seq2) > 0)
            # Vehicle can leave the network and enter again, we must find the original routed segment
            while route_edges[0].from_junction != seq2[0].from_junction:
                route2_edges[indexes2[0]:indexes2[1]] = []
                seq2, indexes2 = graph.road_network.get_longest_sequence(route2_edges)
            assert(route_edges[0].from_junction == seq2[0].from_junction)
            assert(route_edges[-1].to_junction == seq2[-1].to_junction)
            entry2.vehicles[vehicle_id].attributes["route"] = new_scenario.routes_file.add_route(Element("route", {
                "id": route.attrib["id"], "edges": " ".join([edge.id for edge in seq2]),
            }))
            new_scenario.vehicles_file.add_vehicle(entry2.vehicles[vehicle_id].to_xml())
        return new_scenario.save(original_scenario.config_file.get_network())


if __name__ == "__main__":
    scenario_name: str = "itsc_25200_32400"
    tmp: GraphFilter = GraphFilter()
    for color in ["_green", "_red", "_orange"]:
        # tmp.filter_scenario(scenario_name + color, f"DCC{color}", f"{scenario_name + color}_filtered", full_path=False)
        tmp.filter_planned(scenario_name + color + "_filtered", scenario_name + color + "_planned", f"DCC{color}")
    # scenario_name = "lust_25200_32400"
    # for color in ["_lime", "_red", "_orange"]:
    #     # tmp.filter_scenario(scenario_name + color, f"lust{color}", f"{scenario_name + color}_filtered", full_path=False)
    #     tmp.filter_planned(scenario_name + color + "_filtered", scenario_name + color + "_planned", f"lust{color}")
    # for color in ["_green", "_red", "_orange"]:
    #     target: str = scenario_name + color + "_planned2"
    #     tmp.filter_scenario(target, f"DCC{color}", new_scenario_name=f"{target}_filtered", full_path=False)



