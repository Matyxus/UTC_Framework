from utc.src.constants.file_system import FilePaths
from utc.src.plan_qd.parameters.parameter import Parameter
from utc.src.constants.static.process_check import get_max_processes
from typing import List, Dict, Union


class SessionParameters(Parameter):
    """
    Class representing pddl parameters used for sessions of
    scenarios generation
    """
    def __init__(self, file_path: str):
        super().__init__(file_path)

    # ------------------------------ Getters ------------------------------

    # --- Cpu related ---

    def get_process_count(self) -> int:
        """
        :return: the number of processes to be run
        in parallel at the same time
        """
        if isinstance(self.objects["num_processes"], str) and self.objects["num_processes"] == "max":
            return get_max_processes()
        return self.objects["num_processes"]

    def get_thread_count(self) -> int:
        """
        :return: number of allowed threads for multi-threading
        """
        return self.objects["num_threads"]

    def get_time_limit(self) -> int:
        """
        :return: time limit for scenario generation
        """
        return self.objects["timeout"]

    # --- Scenario related ---

    def get_scenario_name(self) -> str:
        """
        :return:
        """
        return self.objects["scenario_name"]

    def get_scenario_count(self) -> int:
        """
        :return: number of scenarios to be generated
        """
        return self.objects["num_scenarios"]

    def get_network(self) -> str:
        """
        :return: name of network
        """
        # Get network name from name of probability file
        if self.objects["network"] is None or self.objects["network"] == "default":
            return self.objects["probability_file"]
        return self.objects["network"]

    def get_seed(self) -> int:
        """
        :return:
        """
        return self.objects["seed"]

    def get_allowed_flows(self) -> List[str]:
        """
        :return:
        """
        return self.objects["flows"]

    def get_flow_count(self) -> int:
        """
        :return: number of flows in scenario
        """
        return self.objects["flow_count"]

    def get_probability_file(self) -> str:
        """
        :return: name of probability file
        """
        return self.objects["probability_file"]

    def get_duration(self) -> int:
        """
        :return: duration of scenario
        """
        return self.objects["duration"]

    # --- Metrics & Graphs related ---

    def get_metrics(self) -> Dict[str, List[str]]:
        """
        :return: allowed metrics
        """
        return self.objects["metrics"]

    def get_c_parameter(self) -> float:
        """
        :return: 'c' parameter of subgraph generation
        """
        return self.objects["c"]

    def get_k_parameter(self) -> Union[int, float, None]:
        """
        :return: 'k' parameter for metrics (list)
        """
        return self.objects["k"]

    # ----- Pddl ----

    def get_pddl_parameters(self) -> dict:
        """
        :return: pddl template for planning
        """
        return self.objects["pddl_params"]

    def check_data(self) -> bool:
        if not self.objects:
            print(f"Session parameters: '{self.file_path}' must be loaded first!")
            return False
        # Compare against template for missing parameters
        template: Parameter = Parameter(FilePaths.SESSSION_TEMPLATE)
        if not template.file_exists(template.file_path):
            print(f"Cannot check data of session parameters: {self.file_path}")
            print(f"Session template file: {FilePaths.SESSSION_TEMPLATE} does not exist!")
            return False
        objects = template.load_data()
        if not objects:
            print(f"Template file is empty!")
            return False
        for key in objects.keys():
            if key not in self.objects:
                print(f"Missing parameter: {key} in session file: {self.file_path}")
                return False
        return True


# For testing purposes
if __name__ == "__main__":
    temp: SessionParameters = SessionParameters("session_template.json")
    temp.add_object("templates", "default")
    temp.add_object("num_scenario", 0)
    temp.add_object("probability_file", None)
    temp.add_object("seed", 42)
    temp.add_object("network", "default")
    temp.add_object("num_cpus", 1)
    temp.add_object("num_threads", 1)
    temp.add_object("time_limit", None)
    temp.add_object("run_mode", "step")
    temp.add_object("save_folder", "default")
    temp.add_object("metrics", "all")
    temp.add_object("flows", "all")
    temp.add_object("k", [10, 20, 30])
    temp.add_object("c", 1.35)
    temp.save()

