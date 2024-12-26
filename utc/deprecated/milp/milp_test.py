from utc.src.utils.task_manager import TaskManager
from utc.src.constants.static import DirPaths, FilePaths, FileExtension
from utc.src.utils.vehicle_extractor import VehicleExtractor, VehicleEntry, Element
from utc.src.constants.file_system.my_directory import MyDirectory
from utc.src.constants.file_system.file_types.sumo_config_file import SumoConfigFile, XmlFile
from utc.src.constants.file_system.file_types.sumo_vehicles_file import SumoVehiclesFile
from utc.src.constants.file_system.file_types.sumo_routes_file import SumoRoutesFile
from utc.src.graph import Graph, RoadNetwork
from typing import Optional, Union, Dict, Tuple, List, Set
import csv

template: List[str] = [
    'name', # name
    'loaded', 'inserted', 'running', 'waiting',  # vehicles
    'total', 'jam', 'yield lane', 'wrong lane', # teleports
    'collisions', 'stops', 'braking',  # safety
    '#vehicles', 'routeLength', 'speed', 'duration', 'waiting time',
    'timeLoss', 'departDelay', 'total travel time', 'total depart delay'
]


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
        resolved_vehicles: set = set()
        previous: str = ""
        for line in pddl_result:
            line = line.rstrip()
            assert(line.startswith("(") and line.endswith(")"))
            line = line[1:-1].split()
            # Extract attributes from list
            car_id: str = line[0]
            if car_id in resolved_vehicles:
                break
            if car_id != previous and previous != "":
                resolved_vehicles.add(previous)
            previous = car_id
            # Add new car
            if car_id not in paths:
                paths[car_id] = []
            paths[car_id].append(line[2][1:])
    return paths


class MilpSenario:
    """
    Class representing mixed integer linear programming scenarios
    """
    def __init__(self, path: str):
        """
        :param path: path to milp scenario folder
        """
        if not MyDirectory.dir_exist(path):
            raise NotADirectoryError(f"Error: {path} is not existing directory!")
        self.path: str = path
        self.name: str = SumoConfigFile.get_file_name(path)
        self.network_dir: MyDirectory = MyDirectory(path + "/maps/networks")
        self.milp_results: MyDirectory = MyDirectory(path + "/results_milp")
        self.simulation_dir: MyDirectory = MyDirectory(path + "/simulation")
        assert(all([self.network_dir.is_loaded(), self.milp_results.is_loaded(), self.simulation_dir.is_loaded()]))
        self.statistics_path: str = self.simulation_dir.dir_path + "/statistics"
        self.statistics_file: str = self.path + "/" + self.name + FileExtension.CSV
        assert(SumoConfigFile.file_exists(self.statistics_file))

    def get_networks(self) -> List[str]:
        """
        :return: List of networks in given MilpScenario
        """
        return MyDirectory.list_directory(self.network_dir.dir_path, True, True, True)

    def get_configs(self) -> List[str]:
        """
        :return: List of configs in given MilpScenario
        """
        return MyDirectory.list_directory(self.simulation_dir.dir_path + "/config", True, True, True)

    def get_results(self) -> Dict[str, List[str]]:
        """
        :return: Mapping of networks names to their corresponding MILP result files
        """
        ret_val: Dict[str, List[str]] = {}
        for sub_dir in MyDirectory.list_directory(self.milp_results.dir_path, False):
            network_name: str = sub_dir.replace("_planned", "_sg")
            ret_val[network_name] = MyDirectory.list_directory(
                self.milp_results.dir_path + f"/{sub_dir}", True, True, True
            )
        return ret_val

    def get_default_routes(self) -> str:
        """
        :return: original route file of scenario
        """
        return MyDirectory(self.path).get_sub_dir("routes").get_file(self.name + FileExtension.SUMO_ROUTES)

    def get_default_config(self) -> str:
        """
        :return:
        """
        return self.simulation_dir.get_sub_dir("config").get_file(self.name + FileExtension.SUMO_CONFIG)

    def get_problems_path(self) -> str:
        """
        :return:
        """
        return self.path + "/problems"


def generate_scenarios(scenario: MilpSenario) -> bool:
    """
    :param scenario:
    :return:
    """
    print(f"------------- Generating scenarios: {scenario.name} -------------")
    original_network: str = (
        "../../../../../maps/sumo/Sydney.net.xml" if "sydney" in scenario.path else
        "../../../../../maps/sumo/New_York.net.xml"
    )
    graph: Graph = Graph(RoadNetwork())
    networks: List[str] = scenario.get_networks()
    results: Dict[str, List[str]] = scenario.get_results()
    extractor: VehicleExtractor = VehicleExtractor(
        SumoVehiclesFile(scenario.get_default_routes()), SumoRoutesFile(scenario.get_default_routes())
    )
    entry: VehicleEntry = extractor.estimate_arrival_naive((0, 3700))
    new_routes: XmlFile = XmlFile(FilePaths.SUMO_ROUTES_TEMPLATE, "r")
    new_config: XmlFile = XmlFile(FilePaths.SUMO_CONFIG_MILP_TEMPLATE, "r")
    error_vehicles: int = 0
    routed_vehicles: int = 0
    for network in networks:
        route_index: int = 0
        routes: Dict[str, str] = {}
        vehicles: Dict[str, str] = {}
        graph.set_network(RoadNetwork())
        assert(graph.loader.load_map(network))
        assert(graph.simplify.simplify_junctions())
        network_name: str = SumoConfigFile.get_file_name(network)
        if network_name not in results:
            continue
        # print(f"Planning on network: {XmlFile.get_file_name(network)}")
        for result_file in results[network_name]:
            # print(f"Parsing result file: {result_file}")
            paths = parse_result(result_file)
            routed_vehicles += len(paths)
            # Parse each vehicle routes, check validity, create XML elements
            for vehicle_id, vehicle_routes in paths.items():
                # print(f"Vehicle: {vehicle_id}, routes: {vehicle_routes}")
                vehicle_edges = graph.road_network.get_edges(vehicle_routes)
                assert(None not in vehicle_edges)
                internal_ids: list = [edge.internal_id for edge in vehicle_edges]
                route_edges = []
                # assert(None not in graph.road_network.get_routes([f"r{r_id}" for r_id in vehicle_routes]))
                for route in graph.road_network.get_routes(internal_ids):
                    # print(f"Route: {route}")
                    assert(route is not None)
                    route_edges.extend(route.get_edge_ids())
                # print(f"Route edges: {route_edges}")
                if not graph.road_network.check_edge_sequence(route_edges):
                    error_vehicles += 1
                    continue
                vehicle_route: str = " ".join(route_edges)
                if vehicle_route not in routes:
                    routes[vehicle_route] = f"r{route_index}"
                    route_index += 1
                assert(vehicle_id not in vehicles)
                vehicles[vehicle_id] = routes[vehicle_route]
        # Add missing vehicles and their routes
        for vehicle_id in (entry.vehicles.keys() ^ vehicles):
            vehicle = entry.vehicles[vehicle_id]
            route = entry.original_routes[vehicle.attributes["route"]]
            if route.attrib["edges"] not in routes:
                routes[route.attrib["edges"]] = route.attrib["id"]
            vehicles[vehicle_id] = routes[route.attrib["edges"]]
        # Add routes and vehicles to file
        for route_edges, route_id in routes.items():
            new_routes.root.append(Element("route", {"id": route_id, "edges": route_edges}))
        i: int = len(new_routes.root)
        for vehicle_id, route_id in vehicles.items():
            vehicle_xml: Element = entry.vehicles[vehicle_id].to_xml()
            vehicle_xml.attrib["route"] = route_id
            new_routes.root.append(vehicle_xml)
        # Save routes & vehicles & config
        file_name: str = network_name.replace("_sg", "_milp_reduced")
        new_routes.root[i:] = sorted(new_routes.root[i:], key=lambda child: float(child.get("depart")))
        assert(new_routes.save(scenario.path + f"/routes/{file_name}" + FileExtension.SUMO_ROUTES))
        new_config.root.find("input").find("net-file").attrib["value"] = original_network
        new_config.root.find("input").find("route-files").attrib["value"] = f"../../routes/{file_name}.rou.xml"
        assert(new_config.save(scenario.simulation_dir.dir_path + f"/config/{file_name}" + FileExtension.SUMO_CONFIG))
        new_routes.root[1:] = []
    if error_vehicles:
        print(f"Error vehicles: {error_vehicles} / {routed_vehicles} in scenario: {scenario.name}!")
    # print(f"Routed vehicles: {routed_vehicles} / {len(entry.vehicles) * len(networks)}")
    print(f"Finished generating results for scenario: {scenario.name}")
    return True


def evaluate_scenario(scenario: MilpSenario, milp_only: bool = True) -> None:
    """
    :param scenario:
    :return:
    """
    print(f"Evaluating scenario: {scenario.name}")
    statistics_dir: str = scenario.simulation_dir.dir_path + "/statistics"
    # -------------------------------- Generate stats --------------------------------
    for config in scenario.get_configs():
        if milp_only and "milp" not in config:
            continue
        xml_file: XmlFile = XmlFile(config, "r")
        for end_element in xml_file.root.find("time").findall("end"):
            xml_file.root.find("time").remove(end_element)
        xml_file.root.find("time").append(Element("end", {"value": "7200"}))
        xml_file.save()
        statistic_file: str = SumoConfigFile.get_file_name(config) + FileExtension.SUMO_STATS
        TaskManager.call_shell_block(
            f"sumo -c {config} --duration-log.statistics true --statistic-output {statistic_file}",
            cwd=statistics_dir
        )
    # -------------------------------- XML results --------------------------------
    stats: List[List[str]] = []
    for statistics_file in MyDirectory.list_directory(statistics_dir, True, True, True):
        if milp_only and "milp" not in statistics_file:
            continue
        xml_file: XmlFile = XmlFile(statistics_file, "r")
        assert(xml_file.is_loaded())
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
    # -------------------------------- CSV results --------------------------------
    rows: List[List[str]] = []
    with open(scenario.statistics_file, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
    assert(len(rows) > 0)
    index: int = 0
    for i in range(-1, -len(rows), -1):
        if rows[i][0] == "name":
            index = len(rows) + i
            break
    assert(index != 0 and rows[index][0] == "name")
    rows[index] = template
    rows[index+1:] = stats
    with open(scenario.statistics_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)
    print(f"Finished evaluating scenario: {scenario.name}")
    return


def together(scenario: MilpSenario) -> None:
    generate_scenarios(scenario)
    evaluate_scenario(scenario)
    return


def generate_task(folder: str) -> None:
    """
    :param folder:
    :return:
    """
    if not MyDirectory.dir_exist(folder):
        return
    task_manager: TaskManager = TaskManager(4)
    for scenario_folder in MyDirectory.list_directory(folder, full_path=True, sort=True):
        scenario: MilpSenario = MilpSenario(scenario_folder)
        task_manager.tasks.append((together, tuple([scenario])))
    task_manager.start()
    return


if __name__ == '__main__':
    folder: str = DirPaths.SCENARIO.format("static_scenarios_reduced_MILPed-fixed")
    generate_task(folder)











