from utc.src.simulator.scenario import Scenario
from utc.src.constants.static import DirPaths, FileExtension, FilePaths
from utc.src.constants.file_system.my_directory import MyDirectory
from utc.src.constants.file_system.file_types.xml_file import XmlFile
from utc.src.constants.file_system.file_types.sumo_config_file import SumoConfigFile
from utc.src.graph import Graph, RoadNetwork
from utc.src.utils.task_manager import TaskManager
from copy import deepcopy
from typing import Tuple, List
import csv


def merge_scenarios(scenarios: List[str], scenario_name: str, sort_vehicles: bool = False) -> bool:
    """
    :param scenarios: list of scenarios name to be merged
    :param scenario_name:
    :param sort_vehicles
    :return:
    """
    print(f"Merging scenarios: {scenarios}")
    if len(scenarios) < 2:
        print("Expected at least 2 scenarios to be merged!")
        return False
    elif MyDirectory.dir_exist(DirPaths.SCENARIO.format(scenario_name), message=False):
        print(f"Cannot create new scenario: {scenario_name}, already exists!")
        return False
    new_scenario: Scenario = Scenario(scenario_name, create_new=True)
    network_file: str = ""
    for name in scenarios:
        scenario: Scenario = Scenario(name)
        if not scenario.exists(True):
            return False
        network_file = scenario.config_file.get_network()
        mapping = new_scenario.routes_file.add_routes(scenario.routes_file.root.findall("route"), re_index=True)
        for vehicle in scenario.vehicles_file.root.findall("vehicle"):
            vehicle.attrib["route"] = mapping[vehicle.attrib["route"]]
            new_scenario.vehicles_file.add_vehicle(vehicle)
    if sort_vehicles:
        new_scenario.vehicles_file.root[1:] = sorted(
            new_scenario.vehicles_file.root[1:], key=lambda x: float(x.attrib["depart"])
        )
    return new_scenario.save(network_file)


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


def find_change(original_edges: str, new_edges: str) -> Tuple[str, str]:
    """
    :param original_edges:
    :param new_edges:
    :return:
    """
    original_list: List[str] = original_edges.split()
    new_list: List[str] = new_edges.split()
    left_index: int = 0
    for i in range(min(len(original_list), len(new_list))):
        if original_list[i] != new_list[i]:
            left_index = i
            break
    right_index: int = 0
    for i in range(-1, -min(len(original_list), len(new_list)) + left_index, -1):
        if original_list[i] != new_list[i]:
            right_index = i+1
            break
    if right_index == 0:
        return " ".join(original_list[left_index:]), " ".join(new_list[left_index:])
    return " ".join(original_list[left_index:right_index]), " ".join(new_list[left_index:right_index])


def merge_planned_scenarios(original: str, scenario_name: str, planned_scenarios: List[str]) -> bool:
    """
    :param original:
    :param planned_scenarios:
    :return:
    """
    print(f"Merging planned scenarios: {planned_scenarios} into original: {original}")
    original_scenario: Scenario = Scenario(original)
    if not original_scenario.exists():
        return False
    scenarios: List[Scenario] = [Scenario(planned_name) for planned_name in planned_scenarios]
    assert(all([scenario.exists() for scenario in scenarios]))
    # Mapping of vehicle ids to their route
    original_mapping: dict = get_mapping(original_scenario)
    # Among all planned scenarios, find which vehicle changed its route
    changes: dict = {
        # Vehicle id : [(replace_seq, by_seq), ...], ....
    }
    for planned_scenario in scenarios:
        print(f"Processing planned scenario: {planned_scenario.name}")
        planned_mapping: dict = get_mapping(planned_scenario)
        assert(len(planned_mapping.keys() & original_mapping.keys()) == len(planned_mapping))
        for vehicle_id, (vehicle, route) in planned_mapping.items():
            # No changes
            if route.attrib["edges"] == original_mapping[vehicle_id][1].attrib["edges"]:
                continue
            # Route was changed
            original_edges: str = original_mapping[vehicle_id][1].attrib["edges"]
            replace_seq, replace_by = find_change(original_edges, route.attrib["edges"])
            assert(original_edges.replace(replace_seq, replace_by) == route.attrib["edges"])
            if vehicle_id not in changes:
                changes[vehicle_id] = []
            changes[vehicle_id].append((replace_seq, replace_by))
    # Generate new scenario
    new_scenario: Scenario = Scenario(scenario_name, create_new=True)
    for vehicle_id, (vehicle, route) in original_mapping.items():
        # Change route
        if vehicle_id in changes:
            for (replace_seq, replace_by) in changes[vehicle_id]:
                if not (replace_seq in route.attrib["edges"]):
                    print(f"Error at vehicle: {vehicle_id}, replacing edge\s: {set(replace_seq.split()) ^ set(replace_by.split())}")
                    continue
                route.attrib["edges"] = route.attrib["edges"].replace(replace_seq, replace_by)
            changes.pop(vehicle_id)
        # Save route to scenario
        route_id: str = new_scenario.routes_file.add_route(route)
        vehicle.attrib["route"] = route_id
        new_scenario.vehicles_file.add_vehicle(vehicle)
    return new_scenario.save(original_scenario.config_file.get_network())


def check_routes(original: str, planned: str) -> bool:
    """
    :param original:
    :param planned:
    :return:
    """
    print(f"Checking scenario: {original}, and planned: {planned}")
    original_scenario: Scenario = Scenario(original)
    planned_scenario: Scenario = Scenario(planned)
    if not original_scenario.exists():
        return False
    elif not planned_scenario.exists():
        return False
    original_mapping: dict = get_mapping(original_scenario)
    planned_mapping: dict = get_mapping(planned_scenario)
    print(len(original_mapping), len(planned_mapping))
    # assert(len(original_mapping.keys() & planned_mapping.keys()) == len(original_mapping.keys()))
    unchanged: int = 0
    changed: int = 0
    first_changed: int = 0
    last_changed: int = 0
    graph: Graph = Graph(RoadNetwork())
    assert(graph.loader.load_map(original_scenario.config_file.get_network()))
    for vehicle, route in planned_mapping.values():
        planned_edges: list = graph.road_network.get_edges(route.attrib["edges"].split())
        assert(None not in planned_edges)
        assert(graph.road_network.check_edge_sequence(planned_edges))
        original_edges: list = graph.road_network.get_edges(original_mapping[vehicle.attrib["id"]][1].attrib["edges"].split())
        assert(None not in original_edges)
        assert(planned_edges[0].from_junction == original_edges[0].from_junction)
        assert(planned_edges[-1].to_junction == original_edges[-1].to_junction)
        first_changed += (planned_edges[0].id != original_edges[0].id)
        last_changed += (planned_edges[-1].id != original_edges[-1].id)
        if route.attrib["edges"] == original_mapping[vehicle.attrib["id"]][1].attrib["edges"]:
            unchanged += 1
        else:
            first, second = find_change(original_mapping[vehicle.attrib["id"]][1].attrib["edges"], route.attrib["edges"])
            assert(
                original_mapping[vehicle.attrib["id"]][1].attrib["edges"].replace(first, second) == route.attrib["edges"]
            )
            changed += 1
    print(f"Changed: {changed}/{len(planned_mapping)} vehicle's routes")
    print(f"Vehicles changed first/last edges: {(first_changed, last_changed)}")
    return True


template: List[str] = [
    'name', # name
    'loaded', 'inserted', 'running', 'waiting',  # vehicles
    'total', 'jam', 'yield lane', 'wrong lane', # teleports
    'collisions', 'stops', 'braking',  # safety
    # VehicleTripsStatistics
    'vehicles', 'routeLength', 'speed', 'duration', 'waiting time',
    'timeLoss', 'departDelay', 'total travel time', 'total depart delay'
]


def print_stats(scenario: Scenario) -> None:
    """
    :param scenario:
    :return:
    """
    assert(scenario.exists())
    stats: List[List[str]] = [template]
    for statistics_file in scenario.scenario_dir.stats.list_dir(True, True, True):
        if not statistics_file.endswith("xml"):
            continue
        xml_file: XmlFile = XmlFile(statistics_file, "r")
        assert (xml_file.is_loaded())
        veh_stats = xml_file.root.find("vehicleTripStatistics").attrib
        veh_stats.pop("departDelayWaiting")
        # Name, vehicles, teleports, safety, TripStatistics
        stats.append(
            [xml_file.get_name()] +
            list(xml_file.root.find("vehicles").attrib.values()) +
            list(xml_file.root.find("teleports").attrib.values()) +
            list(xml_file.root.find("safety").attrib.values()) +
            list(veh_stats.values())
        )
    csv_file: str = scenario.scenario_dir.stats.format_file("results.csv")
    with open(csv_file, 'w+', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(stats)


def generate_configs(scenario: Scenario) -> None:
    """
    :param scenario:
    :return:
    """
    scenario.config_file.save(FilePaths.SCENARIO_CONFIG.format(scenario.name, "stats_routed"))
    end_time = scenario.config_file.root.find("time").find("end")
    scenario.config_file.root.find("time").remove(end_time)
    scenario.config_file.save(FilePaths.SCENARIO_CONFIG.format(scenario.name, "stats_full_routed"))
    # Remove routing
    routing = scenario.config_file.root.find("output")
    scenario.config_file.root.remove(routing)
    scenario.config_file.save(FilePaths.SCENARIO_CONFIG.format(scenario.name, "stats_full"))
    # Add back end time
    scenario.config_file.root.find("time").append(end_time)
    scenario.config_file.save(FilePaths.SCENARIO_CONFIG.format(scenario.name, "stats"))


def generate_statistics(scenarios: List[Scenario]) -> None:
    task_manager: TaskManager = TaskManager(4)
    options: str = "sumo -c {0} -W --duration-log.statistics true --statistic-output {1}.xml"
    for scenario in scenarios:
        generate_configs(scenario)
        assert(scenario.scenario_dir.stats.initialize_dir())
        for config in scenario.scenario_dir.config.list_dir(True, True, True):
            if "stats" not in config:
                continue
            task_manager.tasks.append((
                TaskManager.call_shell_block,
                tuple([options.format(config, XmlFile.get_file_name(config)), scenario.scenario_dir.stats.dir_path])
            ))
    task_manager.start()
    for scenario in scenarios:
        print_stats(scenario)


def prepare_configs(scenarios: List[str], itsc: bool) -> None:
    """
    :param scenarios:
    :return:
    """
    for scenario_name in scenarios:
        scenario: Scenario = Scenario(scenario_name)
        assert(scenario.exists())
        scenario.config_file.set_begin(25200)
        scenario.config_file.set_end(32400)
        if itsc:
            scenario.config_file.set_additional_file(DirPaths.SCENARIO.format("Base") + "/DCC_trafficlights.add.xml")
        else:
            scenario.config_file.set_additional_file(DirPaths.SCENARIO_ADDITIONAL.format("Lust") + "/tll.static.xml")
        scenario.config_file.add_routing()
        scenario.config_file.set_step_length(0.5)
        scenario.config_file.save()


def generate_dump(scenarios: List[Tuple[str, str]], out_file: str, period: int) -> None:
    """
    :param scenarios: (scenario_name, config_name)
    :param out_file: name of output file generated by edge_dump
    :param period: period of tracking statistics
    :return: None
    """
    task_manager: TaskManager = TaskManager(min(len(scenarios), 4))
    options: str = "sumo -c {0} -W"
    for (scenario_name, config_name) in scenarios:
        scenario: Scenario = Scenario(scenario_name)
        assert(scenario.exists())
        dump_file: XmlFile = XmlFile(FilePaths.XmlTemplates.EDGE_DATA)
        data = dump_file.root.find("edgeData")
        data.attrib["file"] = scenario.scenario_dir.stats.format_file(out_file)
        data.attrib["period"] = str(period)
        dump_file.save(DirPaths.SCENARIO_CONFIGS.format(scenario_name) + "/edge_data.add.xml")
        config_path = scenario.scenario_dir.get_config(config_name)
        assert(config_path is not None)
        config: SumoConfigFile = SumoConfigFile(config_path)
        config.set_additional_file(DirPaths.SCENARIO_CONFIGS.format(scenario_name) + "/edge_data.add.xml")
        config.save()
        task_manager.tasks.append((
            TaskManager.call_shell_block,
            tuple([options.format(config_path), scenario.scenario_dir.stats.dir_path])
        ))
    task_manager.start()
    return


if __name__ == "__main__":
    # --- Itsc ---
    # original_scenario: str = "itsc_25200_32400"
    # merge_planned_scenarios(original_scenario, original_scenario + "_planned", [original_scenario + color + "_planned" for color in ["_green", "_red", "_orange"]])
    # planned_scenarios: List[str] = [original_scenario + "_planned"]
    # for color in ["_green", "_red", "_orange"]:
    #     # check_routes(original_scenario + color, original_scenario + color + "_planned")
    #     planned_scenarios.append(original_scenario + color + "_planned")
    # # prepare_configs(planned_scenarios, True)
    # # generate_statistics([Scenario(name) for name in planned_scenarios])
    # scenarios_configs = [(scenario_name, "stats_full") for scenario_name in planned_scenarios]
    # generate_dump(scenarios_configs, "stats_full_edgedata.out.xml", 900)
    # # --- Lust ---
    # original_scenario = "lust_25200_32400"
    # merge_planned_scenarios(original_scenario, original_scenario + "_planned", [original_scenario + color + "_planned" for color in ["_lime", "_red", "_orange"]])
    # planned_scenarios = [original_scenario + "_planned"]
    # for color in ["_lime", "_red", "_orange"]:
    #     planned_scenarios.append(original_scenario + color + "_planned")
    # # prepare_configs(planned_scenarios, False)
    # # generate_statistics([Scenario(name) for name in planned_scenarios])
    # scenarios_configs = [(scenario_name, "stats_full") for scenario_name in planned_scenarios]
    # generate_dump(scenarios_configs, "stats_full_edgedata.out.xml", 900)
    generate_dump(
        [
            ("itsc_25200_32400_planned", "stats_full"),
            # ("lust_25200_32400_planned", "stats_full")
        ],
        "stats_full_edgedata.out.xml",
        900
    )



