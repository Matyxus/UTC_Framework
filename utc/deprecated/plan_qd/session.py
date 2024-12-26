from utc.src.graph.components import Graph, Skeleton
from utc.src.plan_qd.plan_qd_launcher import PlanQDLauncher
from utc.src.pddl import UtcLauncher
from utc.src.simulator import ScenarioMain
from utc.deprecated.ui import CommandParser
from utc.src.plan_qd.parameters import SessionParameters
from utc.src.plan_qd.factories import FlowFactory
from utc.src.constants.file_system import (
    InfoFile, FilePaths, MyFile, SumoConfigFile,
    ProbabilityFile, StatisticsFile, SumoRoutesFile,
    MyDirectory, DirPaths, DefaultDir, ScenarioDir
)
from utc.src.utils import TraciOptions
from datetime import datetime
from pandas import DataFrame
from typing import Dict, List, Tuple, Optional
from numpy import array_equal


class Session:
    """
    Class representing session of scenario generation
    for metrics comparison (requires ".json" file
    as input, containing different parameters)
    """
    def __init__(self):
        self.parameters: Optional[SessionParameters] = None
        self.scenario_dir: Optional[ScenarioDir] = None

    def load_parameters(self, parameters_file: SessionParameters) -> bool:
        """
        :param parameters_file: name of parameter file
        :return: true on success, false otherwise
        """
        if parameters_file is None:
            return False
        # Check data
        self.parameters = parameters_file
        self.parameters.load_data()
        if not parameters_file.check_data():
            return False
        self.parameters = parameters_file
        return True

    def start_generating(self, parameters_file: SessionParameters) -> None:
        """
        Starts automated scenario generation (for comparison of different metrics
        to further simplify sub-graphs)

        :param parameters_file:  name of parameter file
        :return: None
        """
        if not self.load_parameters(parameters_file):
            return
        probability_file: ProbabilityFile = ProbabilityFile(self.parameters.get_probability_file())
        probability_file.read_file()
        finished_scenarios: List[str] = []
        now = datetime.now()
        print(f"Starting to generate: {self.parameters.get_scenario_count()} scenarios, time: {now}")
        for i in range(self.parameters.get_scenario_count()):
            print(f"Starting to generate scenario: {i+1}")
            if not self.generate_default_scenario(probability_file, self.parameters.get_scenario_name()):
                print(f"Unable to generate default scenario, abandoning ...")
                continue
            elif not self.generate_subgraphs(self.scenario_dir.name):
                print(f"Unable to generate sub-graphs for scenario: {self.scenario_dir.name}, abandoning ...")
                continue
            elif not self.generate_plans(self.scenario_dir.name):
                continue
            self.generate_report(self.scenario_dir.name)
            print(f"Finished scenario: {i+1}/{self.parameters.get_scenario_count()}!")
            finished_scenarios.append(self.scenario_dir.name)
            self.parameters.objects["seed"] += 1
        end = datetime.now()
        print(f"Finished generating scenarios, at: {end}, time taken: {end-now}")
        print(f"Generated: {len(finished_scenarios)}/{self.parameters.get_scenario_count()} scenarios")
        print(f"Scenarios: {finished_scenarios}")
        # TODO Generate report about session, time taken, files generated ...

    def generate_default_scenario(self, probability_file: ProbabilityFile, scenario_name: str) -> bool:
        """

        :param probability_file: probability file to be used for generating flows
        :param scenario_name: name of scenario (current time will be added as prefix
        -> [hour_minute_second]_[scenario_name]), if scenario name is not given,
        name of probability file will be used
        :return: true on success, false otherwise
        """
        # Suffix for scenario (current time)
        scenario_name = (scenario_name if scenario_name else probability_file.get_file_name(probability_file))
        scenario_name = str(datetime.now().time().replace(microsecond=0)).replace(":", "_") + "_" + scenario_name
        print(f"Generating default scenario: '{scenario_name}'")
        # Already exists
        if MyDirectory.dir_exist(DirPaths.SCENARIO.format(scenario_name), message=False):
            print(f"Directory named: '{scenario_name}', scenario already exists, abandoning generation ..")
            return False
        # Scenario
        scenario_main: ScenarioMain = ScenarioMain(log_commands=True)
        print(f"Using network: {self.parameters.get_network()}")
        scenario_main.generate_scenario_command(scenario_name, self.parameters.get_network())
        # Flows
        print(f"Generating flows")
        flow_factory: FlowFactory = FlowFactory(
            scenario_main.scenario_generator.graph, probability_file,
            allowed_flows=self.parameters.get_allowed_flows(),
            seed_num=self.parameters.get_seed()
        )
        _, flow_methods = scenario_main.scenario_generator.vehicle_factory.vehicle_flows.get_methods()[0]
        for flow_name, flow_args in flow_factory.generate_flows(
                0, self.parameters.get_duration(), self.parameters.get_flow_count(),
                ):
            print(f"Generated flow: {flow_name}, args: {flow_args}")
            flow_methods[flow_name](*flow_args)
        scenario_main.save_scenario_command()
        success: bool = MyFile.file_exists(FilePaths.SCENARIO_CONFIG.format(scenario_name, scenario_name))
        if success:
            self.set_scenario_dir(scenario_name)
        print(f"Finished generating default scenario, success: {success}")
        return success

    def generate_subgraphs(self, scenario_name: str) -> bool:
        """
        :return: true on success, false otherwise
        """
        # ---------------- Init  ----------------
        self.set_scenario_dir(scenario_name)
        print(f"Generating default sub-graphs for scenario: '{scenario_name}'")
        # Parse ".info" file of scenario
        commands_order, commands = InfoFile(FilePaths.SCENARIO_INFO.format(scenario_name, scenario_name)).load_data()
        # Checks
        if commands_order is None or commands is None:
            print(f"Invalid scenario name passed to method: 'generate_subgraphs' !")
            return False
        network_name: str = CommandParser.parse_args_text(commands["generate_scenario"][0])["network_name"]
        graph_main: PlanQDLauncher = PlanQDLauncher(log_commands=True)
        graph_main.load_graph_command(network_name)
        graph_main.simplify_command(network_name)
        parameter_c: float = self.parameters.get_c_parameter()
        # ---------------- Create default subgraph  ----------------
        paths: List[Tuple[str, str]] = []
        # Get flow paths
        for command_name, command_args in commands.items():
            if "flow" not in command_name:
                continue
            for command_arg in command_args:
                args_mapping: Dict[str, str] = CommandParser.parse_args_text(command_arg)
                paths.append((args_mapping["from_junction_id"], args_mapping["to_junction_id"]))
        # Create default sub-graph
        for index, (from_junction, to_junction) in enumerate(paths):
            ret_val = graph_main.subgraph_command(
                f"sg{index}", network_name,
                from_junction, to_junction,
                parameter_c
            )
            # Unable to generate default sub-graph
            if ret_val is None:
                return False
        default_subgraph = scenario_name + "_default_sg"
        print(f"Successfully generated default subgraph: {default_subgraph}")
        # Create subgraph for metric
        if "similarity_metric" in self.parameters.get_metrics():
            ret = graph_main.similarity_factory(
                self.parameters.get_metrics()["similarity_metric"], self.scenario_dir.name,
                default_subgraph, self.parameters.get_k_parameter(),
                self.parameters.get_process_count()
            )
            if ret is None:
                return False
            for success, _ in ret:
                if not success:
                    return False
        # Free memory of routes
        graph_main.subgraph_routes = None
        # Merge default subgraph
        for i in range(1, len(paths)):
            graph_main.merge_command("sg0", f"sg0", f"sg{i}")
        # Save
        graph_main.save_graph_command("sg0", default_subgraph, scenario_name=self.scenario_dir.name)
        return MyFile.file_exists(FilePaths.SCENARIO_MAP.format(scenario_name, default_subgraph))

    def generate_plans(self, scenario_name: str = "") -> bool:
        """
        :return: true on success, false otherwise
        """
        self.set_scenario_dir(scenario_name)
        network_dir: Optional[DefaultDir] = self.scenario_dir.map_dir.get_sub_dir("networks")
        if not network_dir:
            print(f"Networks directory does not exist")
            return False
        sub_graphs: Optional[List[str]] = network_dir.get_files()
        if not sub_graphs:
            print(f"Networks folder is empty!")
            return False
        print(
            f"Generating plans for scenario: '{scenario_name}'\n"
            f"from graphs: '{sub_graphs}'\n"
            f"total: {len(sub_graphs)}."
        )
        pddl_parameters: dict = self.parameters.get_pddl_parameters()
        utc_launcher: UtcLauncher = UtcLauncher()
        for index, sub_graph in enumerate(sub_graphs):
            if not sub_graph.endswith("_sg"):
                print(f"Invalid subgraph: {sub_graph}, does not end with '_sg'")
                continue
            new_scenario: str = sub_graph.replace("_sg", "_planned")
            utc_launcher.initialize_command(new_scenario, scenario_name, sub_graph)
            utc_launcher.generate_problems_command(pddl_parameters["domain"], pddl_parameters["window"])
            utc_launcher.generate_results_command(
                pddl_parameters["planner"], pddl_parameters["domain"],
                pddl_parameters["timeout"], self.parameters.get_process_count()
            )
            utc_launcher.generate_scenario_command()
            print(f"Finished planning on subgraph: {sub_graphs}, {index+1}/{len(sub_graphs)}")
        return True

    def generate_report(self, scenario_name: str) -> None:
        """
        :return:
        """
        self.set_scenario_dir(scenario_name)
        print(f"Generating report for scenario: {scenario_name}")
        # ------------------------ Construct graph comparison ------------------------
        sub_graphs: List[str] = self.scenario_dir.map_dir.get_sub_dir("networks").get_files(
            full_path=True, extension=True
        )
        # Add original network
        network: str = SumoConfigFile(FilePaths.SCENARIO_CONFIG.format(scenario_name, scenario_name)).get_network()
        sub_graphs.insert(0, FilePaths.MAP_SUMO.format(network))
        if not sub_graphs:
            print(f"Networks folder is empty!")
            return
        data: Dict[str, List[str]] = {
            "name": [],
            "junctions": [],
            "edges": [],
            "length": []
        }
        for sub_graph in sorted(sub_graphs):
            graph: Graph = Graph(Skeleton())
            if not graph.loader.load_map(sub_graph):
                return
            sub_graph = MyFile.get_file_name(sub_graph)
            sub_graph = sub_graph.replace(scenario_name + "_", "")
            data["name"].append(sub_graph)
            data["junctions"].append(str(len(graph.skeleton.junctions.keys())))
            data["edges"].append(str(len(graph.skeleton.edges.keys())))
            data["length"].append(str(graph.skeleton.get_network_length()))
        graphs_stats: DataFrame = DataFrame(data)
        print(f"Finished creating graph comparison")
        # ------------------------  Construct planning comparison ------------------------
        print(f"Generating planning comparison")
        data: Dict[str, List[str]] = {
            "name": [],
            "total_results": [],
            "initial_results": [],
            "problem_count": []
        }
        plan_dirs: List[DefaultDir] = [
            DefaultDir(dir_name, self.scenario_dir.results_dir.path)
            for dir_name in self.scenario_dir.results_dir.get_files()
            # get_files() will return directories
        ]
        for plan_dir in plan_dirs:
            print(f"Parsing result files of dir: {plan_dir.name}")
            data["name"].append(plan_dir.name)
            plan_files: List[str] = plan_dir.get_files()
            data["total_results"].append(str(len(plan_files)))
            # initial result files
            data["initial_results"].append(str(len(set(plan_files))))
            data["problem_count"].append(
                str(len(self.scenario_dir.problems_dir.get_sub_dir(plan_dir.name).get_files()))
            )
            # val: float = MyFile.get_edit_time(result_file)
            # edit_time: str = datetime.fromtimestamp(val).strftime('%Y-%m-%d %H:%M:%S')
        plans_stats: DataFrame = DataFrame(data)
        print(f"Finished creating plans comparison")
        # ------------------------  Construct information about vehicles ------------------------
        print(f"Generating vehicles comparison")
        data: Dict[str, List[str]] = {
            "flow_name": [],
            "from": [],
            "to": [],
            "duration": [],
            "per_minute": [],
            "total": []
        }
        commands_order, commands = InfoFile(FilePaths.SCENARIO_INFO.format(scenario_name, scenario_name)).load_data()
        # Count how many vehicles use each rout
        sumo_routes: SumoRoutesFile = SumoRoutesFile(FilePaths.SCENARIO_ROUTES.format(scenario_name, scenario_name))
        routes: Dict[str, dict] = {}
        for route in sumo_routes.root.findall("route"):
            routes[route.attrib["id"]] = {
                "from": route.attrib["fromJunction"],
                "to": route.attrib["toJunction"],
                "count": 0
            }
        for vehicle in sumo_routes.root.findall("vehicle"):
            if vehicle.attrib["route"] in routes:
                routes[vehicle.attrib["route"]]["count"] += 1
        # Get flow paths
        for command_name, command_args in commands.items():
            if "flow" not in command_name:
                continue
            # Multiple same named flows
            for flow_args in command_args:
                data["flow_name"].append(command_name)
                args_mapping: Dict[str, str] = CommandParser.parse_args_text(flow_args)
                data["from"].append(args_mapping["from_junction_id"])
                data["to"].append(args_mapping["to_junction_id"])
                data["duration"].append(str(int(args_mapping["end_time"]) - int(args_mapping["start_time"])))
                for route, route_attrib in routes.items():
                    if route_attrib["from"] == data["from"][-1] and route_attrib["to"] == data["to"][-1]:
                        data["total"].append(str(route_attrib["count"]))
                        data["per_minute"].append(
                            str(round(route_attrib["count"] / round(int(data["duration"][-1]) / 60, 2), 1))
                        )
                        break
        vehicles_stats: DataFrame = DataFrame(data)
        print(f"Finished creating plans comparison")
        # ------------------------  Construct scenario statistics comparison ------------------------
        scenarios: List[str] = sorted(
            self.scenario_dir.simulation_dir.config_dir.get_files(extension=True, full_path=True)
        )
        # Generate statistics and record vehicle statistics
        traci_options: TraciOptions = TraciOptions()
        print(f"Generating statistics for scenarios")
        data: Dict[str, List[str]] = {
            "name": []
        }
        for scenario_path in scenarios:
            scenario_path = MyFile.get_file_name(scenario_path)
            command: str = "sumo " + " ".join(traci_options.get_all(scenario_path, scenario_name))
            success, _ = UtcLauncher.call_shell(command, message=False)
            if not success:
                print(f"Error at generating statistics for scenario: {scenario_path}")
                continue
            statistic_file: StatisticsFile = StatisticsFile(
                FilePaths.SCENARIO_STATISTICS.format(scenario_name, scenario_path)
            )
            if not statistic_file.is_loaded():
                continue
            if scenario_path != scenario_name:
                scenario_path = scenario_path.replace(scenario_name + "_", "")
            data["name"].append(scenario_path)
            for key, value in statistic_file.get_vehicle_stats().items():
                if key not in data:
                    data[key] = []
                data[key].append(value)
        scenario_stats: DataFrame = DataFrame(data)
        print(f"Finished generating statistics")
        graphs_stats.to_csv(FilePaths.SCENARIO_COMPARISON.format(scenario_name, scenario_name), index=False)
        vehicles_stats.to_csv(FilePaths.SCENARIO_COMPARISON.format(scenario_name, scenario_name), index=False, mode="a")
        plans_stats.to_csv(FilePaths.SCENARIO_COMPARISON.format(scenario_name, scenario_name), index=False, mode="a")
        scenario_stats.to_csv(FilePaths.SCENARIO_COMPARISON.format(scenario_name, scenario_name), index=False, mode="a")

    # ----------------------------------------------- Utils -----------------------------------------------

    def set_scenario_dir(self, scenario_name: str) -> None:
        """
        :param scenario_name:
        :return:
        """
        if self.scenario_dir is None or self.scenario_dir.name != scenario_name:
            self.scenario_dir = ScenarioDir(scenario_name)
            self.scenario_dir.initialize_dir_structure()

    def test_parallel_matrix(self, scenario_name: str) -> None:
        """
        :param scenario_name:
        :return:
        """
        self.set_scenario_dir(scenario_name)
        print(f"Generating default sub-graphs for scenario: '{scenario_name}'")
        # Parse ".info" file of scenario
        commands_order, commands = InfoFile(FilePaths.SCENARIO_INFO.format(scenario_name, scenario_name)).load_data()
        network_name: str = CommandParser.parse_args_text(commands["generate_scenario"][0])["network_name"]
        graph_main: PlanQDLauncher = PlanQDLauncher(log_commands=True)
        graph_main.load_graph_command(network_name)
        graph_main.simplify_command(network_name)
        parameter_c: float = self.parameters.get_c_parameter()
        # ---------------- Create default subgraph  ----------------
        paths: List[Tuple[str, str]] = []
        # Get flow paths
        for command_name, command_args in commands.items():
            if "flow" not in command_name:
                continue
            for command_arg in command_args:
                args_mapping: Dict[str, str] = CommandParser.parse_args_text(command_arg)
                paths.append((args_mapping["from_junction_id"], args_mapping["to_junction_id"]))
        # Create sub-graphs
        for index, (from_junction, to_junction) in enumerate(paths):
            ret_val = graph_main.subgraph_command(
                f"sg{index}", network_name,
                from_junction, to_junction,
                parameter_c
            )
            if index == 2:
                mat_A = graph_main.similarity_metric.create_jaccard_matrix_parallel(ret_val, 4)
                mat_B = graph_main.similarity_metric.create_jaccard_matrix(ret_val)
                # print(DataFrame(mat_A))
                print(array_equal(mat_A, mat_B))
                quit()


if __name__ == "__main__":
    import sys
    sys.setrecursionlimit(10000)
    session: Session = Session()
    session.start_generating(SessionParameters("dejvice_session"))


