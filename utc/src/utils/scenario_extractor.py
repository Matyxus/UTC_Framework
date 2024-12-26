import time
from utc.src.simulator import Scenario
from utc.src.simulator.simulation import Simulation
from utc.src.constants.static import DirPaths, FilePaths, FileExtension
from utc.src.constants.file_system import SumoConfigFile
from utc.src.graph.network import Graph, RoadNetwork
from utc.src.utils.vehicle_extractor import VehicleExtractor
from typing import Optional, Union, Dict, Tuple, List, Set
from copy import deepcopy


class ScenarioExtractor:
    """
    Extract (and generate) scenarios from already existing scenario (custom made, or
    downloaded from internet). Provides option to filter vehicles on given network,
    include snapshots, etc.
    """

    def __init__(self):
        # Simulation
        self.config: Optional[SumoConfigFile] = None
        self.scenario: Optional[Scenario] = None
        self.graph: Optional[Graph] = None

    def merge_scenario(
            self, scenario_name: str, filtered_scenario_name: str = "",
            planned_scenario_name: str = "", new_scenario_name: str = ""
        ) -> bool:
        """
        Merges result of planned scenario (on sub-graph), with original scenario

        :param scenario_name: original scenario
        :param filtered_scenario:
        :param planned_scenario:  scenario which was planned from original (on sub-graph)
        :param new_scenario: name of newly created scenario
        :return: True on success, False otherwise
        """
        filtered_scenario_name = filtered_scenario_name if filtered_scenario_name else scenario_name + "_filtered"
        planned_scenario_name = planned_scenario_name if planned_scenario_name else filtered_scenario_name + "_planned"
        new_scenario_name = new_scenario_name if new_scenario_name else scenario_name + "_merged"
        self.scenario = Scenario(scenario_name)
        self.graph = Graph(RoadNetwork())
        filtered_scenario: Scenario = Scenario(filtered_scenario_name)
        planned_scenario: Scenario = Scenario(planned_scenario_name)
        if not self.scenario.exists() and filtered_scenario.exists() and planned_scenario.exists():
            return False
        elif not self.graph.loader.load_map(self.scenario.config_file.get_network()):
            return False
        new_scenario: Scenario = Scenario(new_scenario_name, create_new=True)

        def get_mapping(scenario: Scenario) -> dict:
            """
            :param scenario:
            :return:
            """
            routes: dict = {
                route.attrib["id"]: route for route in scenario.routes_file.root.findall("route")
            }
            return {vehicle.attrib["id"]: routes[vehicle.attrib["route"]] for vehicle in scenario.vehicles_file.root.findall("vehicle")}

        original_mapping: dict = get_mapping(self.scenario)
        filtered_mapping: dict = get_mapping(filtered_scenario)
        planned_mapping: dict = get_mapping(planned_scenario)
        # Add vehicles and routes to new scenario
        skipped: int = 1
        for original_vehicle in self.scenario.vehicles_file.root.findall("vehicle"):
            original_vehicle = deepcopy(original_vehicle)
            route = deepcopy(original_mapping[original_vehicle.attrib["id"]])
            vehicle_id: str = original_vehicle.attrib["id"]
            # For vehicle new planned route was found, change original
            if vehicle_id in planned_mapping:
                filtered_route = filtered_mapping[vehicle_id]
                planned_route = planned_mapping[vehicle_id]
                assert(filtered_route.attrib["edges"] in route.attrib["edges"])
                new_edges: str = route.attrib["edges"].replace(
                    filtered_route.attrib["edges"], planned_route.attrib["edges"]
                )
                if not self.graph.road_network.check_edge_sequence(new_edges.split()):
                    print(f"Skipping assignment for vehicle: {vehicle_id}, count: {skipped}")
                    skipped += 1
                else:
                    route.attrib["edges"] = new_edges
            original_vehicle.attrib["route"] = new_scenario.routes_file.add_route(route)
            new_scenario.vehicles_file.add_vehicle(original_vehicle)
        return new_scenario.save(self.scenario.config_file.get_network())

    def merge_planned_scenarios(self, original_scenario: str, new_scenario: str, planned_scenarios: List[str]) -> bool:
        """
        :param original_scenario:
        :param new_scenario
        :param planned_scenarios:
        :return:
        """
        scenario: Scenario = Scenario(original_scenario)
        new_scenario: Scenario = Scenario(new_scenario, create_new=True)
        planned_vehicles: Set[str] = set()


        def get_mapping(scenario: Scenario) -> dict:
            """
            :param scenario:
            :return:
            """
            routes: dict = {
                route.attrib["id"]: route for route in scenario.routes_file.root.findall("route")
            }
            return {vehicle.attrib["id"]: routes[vehicle.attrib["route"]] for vehicle in scenario.vehicles_file.root.findall("vehicle")}

        # Vehicle to route id
        mapping: dict = get_mapping(scenario)

        # Merge planned paths
        for planned_scenario_name in planned_scenarios:
            planned_scenario: Scenario = Scenario(planned_scenario_name)
            planned_mapping: dict = get_mapping(planned_scenario)
            for vehicle_id, route in planned_mapping:
                assert(vehicle_id in mapping)
                # Merge routes


        # Add all vehicles and routes to new scenario
        for vehicle in scenario.vehicles_file.root.findall("vehicle"):
            new_scenario.routes_file.add_route(routes[vehicle.attrib["route"]], re_index=False)
            new_scenario.vehicles_file.add_vehicle(vehicle)
        # Save
        return new_scenario.save(scenario.config_file.get_network())

    def split_scenario(self, scenario_name: str, new_scenario_name: str, time_frame: Tuple[float, float]) -> bool:
        """
        :param scenario_name: name of scenario from which to extract vehicles & routes
        :param new_scenario_name: name of newly generated scenario
        :param time_frame: initial and end time of vehicle
        :return: True on success, False otherwise
        """
        self.scenario = Scenario(scenario_name)
        if not self.scenario.exists():
            return False
        new_scenario = Scenario(new_scenario_name, create_new=True)
        vehicle_extractor: VehicleExtractor = VehicleExtractor(self.scenario.vehicles_file, self.scenario.routes_file)
        entry = vehicle_extractor.estimate_arrival_naive(time_frame)
        if entry is None or not entry.vehicles:
            return False
        new_scenario.routes_file.add_routes(deepcopy(list(entry.original_routes.values())), re_index=False)
        new_scenario.vehicles_file.add_vehicles([vehicle.to_xml() for vehicle in entry.vehicles.values()])
        return new_scenario.save(self.scenario.config_file.get_network())

    def extract_scenario(
            self, config_path: Union[str, SumoConfigFile], scenario_name: str,
            from_state: str = "", network: str = None, from_time: int = 0,
            to_time: int = -1, use_vehicle_time: bool = True,
            snapshots: bool = True, estimate_flows: bool = False
        ) -> bool:
        """
        :param config_path: path to configuration file
        :param scenario_name: name of newly generated scenario (time will be added as suffix)
        :param from_state: if scenario should be loaded from certain state
        :param network: if new scenario should only be on certain sub-network
        :param from_time: starting time
        :param to_time: ending time
        :param use_vehicle_time: if ending time should be measured by last car departure
        :param snapshots: if snapshot should be included in scenario
        :param estimate_flows: if vehicle flow file should be generated
        :return: True on success, false otherwise
        """
        scenario_name += f"_{from_time}_{to_time}"
        with Simulation(config_path, {"-W": ""}, from_state) as simulation:
            if simulation is None or not simulation.is_running():
                return False
            # Initialize scenario
            self.scenario = Scenario(scenario_name, create_new=True)
            print(f"Starting simulation at time: {simulation.get_time(False)}")
            total_steps: int = 0
            while simulation.is_running() and simulation.get_time(use_vehicle_time) < to_time:
                # Get routes from loaded vehicles, filter based on their edges and change ids
                new_routes_ids: Dict[str, str] = self.scenario.routes_file.add_routes(simulation.get_routes())
                # Get loaded vehicles each step
                for vehicle in simulation.get_vehicles():
                    # Change vehicle ids to new ids
                    vehicle.attrib["route"] = new_routes_ids[vehicle.attrib["route"]]
                    self.scenario.vehicles_file.add_vehicle(vehicle)
                simulation.step()
                total_steps += 1
                if total_steps % 10 == 0:
                    print(f"Current time: {simulation.get_time(False)}")
            # Save scenario
            if not self.scenario.save(FilePaths.MAP_SUMO.format("DCC"), True):
                return False
            # Save scenario
            if snapshots:
                simulation.save_snapshot(FilePaths.SCENARIO_SNAPSHOT.format(scenario_name, scenario_name))
        return True

    def extract_scenarios(
            self, config_path: str, scenario_name: str, period: int = 3600,
            from_state: str = "", network: str = None, from_time: int = 0,
            to_time: int = -1, use_vehicle_time: bool = True,
            snapshots: bool = True, estimate_flows: bool = True
        ) -> bool:
        """
        :param config_path: path to configuration file
        :param scenario_name: name of newly generated scenario (time will be added as suffix)
        :param period: how often should scenarios be created (seconds), default 1 hour
        :param from_state: if scenario should be loaded from certain state
        :param network: if new scenario should only be on certain sub-network
        :param from_time: starting time
        :param to_time: ending time
        :param use_vehicle_time: if ending time should be measured by last car departure
        :param snapshots: if snapshot should be included in scenario
        :param estimate_flows: if vehicle flow file should be generated
        :return: True on success, false otherwise
        """
        if not (period > 0):
            print(f"Invalid period, must be higher than 0, got: {period}!")
            return False
        self.config = SumoConfigFile(config_path)
        to_time = self.config.get_end_time() if to_time == -1 else min(self.config.get_end_time(), to_time)
        if not self.config.is_loaded():
            return False
        elif period > (self.config.get_end_time() - self.config.get_start_time()):
            print(f"Invali period, higher then entire simulation time!")
            return False
        total_scenarios: int = (to_time - from_time) // period
        print(f"Proceeding to generate {total_scenarios} scenarios")

        for i in range(total_scenarios):
            now: float = time.time()
            if not self.extract_scenario(
                    self.config, scenario_name, from_state, network,
                    from_time, from_time + period, use_vehicle_time,
                    snapshots, estimate_flows
                    ):
                return False
            from_state = FilePaths.SCENARIO_SNAPSHOT.format(
                scenario_name + f"_{from_time}_{from_time + period}",
                scenario_name + f"_{from_time}_{from_time + period}"
            )
            assert(SumoConfigFile.file_exists(from_state))
            from_time += period
            print(f"Finished extracting scenario: {i+1}/{total_scenarios}")
            print(f"Time taken: {round(time.time() - now)}s")
        return True


# For testing purposes
if __name__ == "__main__":
    config_path: str = (DirPaths.SCENARIO.format("Base") + "/DCC_simulation" + FileExtension.SUMO_CONFIG)
    temp: ScenarioExtractor = ScenarioExtractor()
    temp.split_scenario("Lust", "lust_25200_32400", (25200, 32400))
    quit()
    # temp.split_scenario("itsc", "itsc_18000_28800", (18000, 28800))
    # temp.extract_scenario(config_path, "itsc", from_time=72000, to_time=75600, use_vehicle_time=False, snapshots=True)
    # temp.merge_scenario("itsc_18000_21600")
    # temp.merge_scenario("itsc_21600_25200")
    # temp.merge_scenario("itsc_25200_28800")
    # temp.merge_scenario("itsc", "itsc_21600_25200", (21600, 25200))
    # temp.merge_scenario("itsc", "itsc_25200_28800", (25200, 28800))
    temp.extract_scenarios(
        config_path, "itsc", period=3600, from_state=FilePaths.SCENARIO_SNAPSHOT.format("itsc_72000_75600", "itsc_72000_75600"),
        from_time=75600, to_time=79200, use_vehicle_time=False
    )


