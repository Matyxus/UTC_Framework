from utc.src.clustering.gravitational.congestion_visualizer import CongestionVisualizer
from utc.src.constants.static.file_constants import DirPaths, FileExtension
from utc.src.graph import Graph, RoadNetwork
from utc.src.simulator.scenario import Scenario
from utc.src.utils.vehicle_extractor import VehicleExtractor, VehicleEntry
from typing import Dict, Tuple, Optional, List
import numpy as np
from copy import deepcopy

def get_mapping(scenario: Scenario) -> dict:
    """
    :param scenario:
    :return:
    """
    routes: dict = {route.attrib["id"]: route for route in scenario.routes_file.root.findall("route")}
    return {
        vehicle.attrib["id"]: (vehicle, deepcopy(routes[vehicle.attrib["route"]]))
        for vehicle in scenario.vehicles_file.root.findall("vehicle")
    }

def find_contrib(scenarios: List[Scenario], graph: Graph) -> None:
    """
    :param scenarios: planned and original scenario
    :param graph: of the graph
    :return: None
    """
    visualizer: CongestionVisualizer = CongestionVisualizer()
    planned, orig = scenarios[0], scenarios[1]
    # Get CI
    planned_array = visualizer.load_ci(planned.scenario_dir.stats.get_file("stats_full_edgedata.out.xml"), graph)
    orig_array = visualizer.load_ci(orig.scenario_dir.stats.get_file("stats_full_edgedata.out.xml"), graph)
    diff = (planned_array - orig_array)
    # Find all vehicles which routes have been changed
    planned_mapping: dict = get_mapping(planned)
    original_mapping: dict = get_mapping(orig)
    assert(len(planned_mapping) == len(original_mapping))
    changed: int = 0
    # Values
    small_diff: int = 0
    medium_diff: int = 0
    high_diff: int = 0

    for vehicle, route in planned_mapping.values():
        orig_route = original_mapping[vehicle.attrib["id"]][1]
        if route.attrib["edges"] == orig_route.attrib["edges"]:
            continue
        # Find out if this vehicle contributed to the improved regions
        internal_ids: np.ndarray = np.array(
            [edge.internal_id for edge in graph.road_network.get_edges(route.attrib["edges"].split())]
        )
        vals = diff[internal_ids]
        small_diff += (np.sum(vals < -0.25) != 0)
        medium_diff += (np.sum(vals < -0.5) != 0)
        high_diff += (np.sum(vals < -0.75) != 0)
        changed += 1
    print(f"Changed vehicles: {changed}, ci: {small_diff, medium_diff, high_diff}")
    return


if __name__ == '__main__':
    network: str = "DCC"
    graph: Graph = Graph(RoadNetwork())
    if not graph.loader.load_map(network):
        raise FileNotFoundError(f"Error unable to locate network: '{network}'")
    find_contrib([Scenario("itsc_25200_32400_planned"), Scenario("itsc_25200_32400")], graph)




