from utc.src.utils.task_manager import TaskManager
from utc.src.constants.static import DirPaths, FilePaths, FileExtension
from utc.src.utils.vehicle_extractor import VehicleExtractor, VehicleEntry, Element
from utc.src.simulator.scenario import Scenario
from utc.src.constants.file_system.my_directory import MyDirectory
from utc.src.constants.file_system.file_types.sumo_config_file import SumoConfigFile, XmlFile
from utc.src.constants.file_system.file_types.sumo_vehicles_file import SumoVehiclesFile
from utc.src.constants.file_system.file_types.sumo_routes_file import SumoRoutesFile
from utc.src.pddl.traffic.network_builder import NetworkBuilder, PddlHandler
from utc.src.pddl.traffic.pddl_problem import PddlProblem
from utc.src.graph import Graph, RoadNetwork, Route
from copy import deepcopy
from typing import Optional, Union, Dict, Tuple, List, Set


def parse_result(result_path: str) -> Optional[Dict[str, List[str]]]:
    """
    :param result_path: path of pddl result file
    :return: Dictionary mapping vehicle id (abstract) to list of route id's (internal)
    """
    paths: Dict[str, List[str]] = {
        # car_id : [list of routes], ...
    }
    # Check
    if not SumoRoutesFile.file_exists(result_path):
        return None
    with open(result_path, "r") as pddl_result:
        for line in pddl_result:
            line = line.rstrip()
            assert(line.startswith("(") and line.endswith(")"))
            line = line[1:-1].split()
            # Extract attributes from list
            car_id: str = line[0]
            # Add new car
            if car_id not in paths:
                paths[car_id] = []
            paths[car_id].append(line[2])
    return paths




if __name__ == '__main__':
    graph: Graph = Graph(RoadNetwork())
    scenario_name: str = "13_06_58_sydney_increasing_planned"
    assert(graph.loader.load_map("13_06_58_sydney_increasing_default_sg"))
    scenario: Scenario = Scenario(scenario_name)
    extractor: VehicleExtractor = VehicleExtractor(scenario.vehicles_file, scenario.routes_file)
    vehicle_paths = {}
    for result_file in scenario.scenario_dir.get_sub_dir("results2").list_dir(True, True, True):
        name: str = SumoRoutesFile.get_file_name(result_file)
        interval: str = name.replace("result_", "")
        start_time, end_time = map(int, interval.split("_"))
        entry: VehicleEntry = extractor.estimate_arrival_naive((start_time, end_time))
        vehicle_names: List[str] = list(entry.vehicles.keys())
        paths = parse_result(result_file)
        assert(len(paths) == len(entry.vehicles))
        for vehicle, routes in paths.items():
            v_id: str = vehicle_names[int(vehicle.replace("v", ""))]
            vehicle_paths[v_id] = routes
    print(f"Routed vehicles: {len(vehicle_paths)}")
    entry: VehicleEntry = extractor.estimate_arrival_naive((0, 3700))
    new_routes: SumoRoutesFile = SumoRoutesFile()
    new_vehicles: SumoVehiclesFile = SumoVehiclesFile()
    new_config: SumoConfigFile = SumoConfigFile()
    counter: int = 0
    for vehicle, routes in vehicle_paths.items():
        edges = []
        for route in graph.road_network.get_routes(routes):
            edges.extend(route.edge_list)
        assert(graph.road_network.check_edge_sequence(edges))
        og_route = entry.original_routes[entry.vehicles[vehicle].attributes["route"]]
        og_edges = graph.road_network.get_edges(og_route.attrib["edges"].split())
        assert(og_edges[0].from_junction == edges[0].from_junction)
        assert(og_edges[-1].to_junction == edges[-1].to_junction)
        route_id = new_routes.add_route(Route(edges, attributes={"id": f"r{counter}", "edges": ""}).to_xml())
        entry.vehicles[vehicle].attributes["route"] = route_id
        new_vehicles.add_vehicle(entry.vehicles[vehicle].to_xml())
        counter += 1
    # Add missing
    for vehicle in (entry.vehicles.keys() ^ vehicle_paths):
        og_route = entry.original_routes[entry.vehicles[vehicle].attributes["route"]]
        entry.vehicles[vehicle].attributes["route"] = new_routes.add_route(og_route)
        new_vehicles.add_vehicle(entry.vehicles[vehicle].to_xml())
    new_vehicles.root[1:] = sorted(new_vehicles.root[1:], key=lambda child: float(child.get("depart")))
    # Set config vals
    new_config.set_network_file(FilePaths.MAP_SUMO.format("Sydney"))
    new_config.set_routes_file(FilePaths.SCENARIO_ROUTES.format(scenario_name, "milp_reduced_fixed"))
    new_config.set_additional_file(FilePaths.SCENARIO_VEHICLES.format(scenario_name, "milp_reduced_fixed"))
    # Save
    new_vehicles.save(FilePaths.SCENARIO_VEHICLES.format(scenario_name, "milp_reduced_fixed"))
    new_routes.save(FilePaths.SCENARIO_ROUTES.format(scenario_name, "milp_reduced_fixed"))
    new_config.save(FilePaths.SCENARIO_CONFIG.format(scenario_name, "milp_reduced_fixed"))






