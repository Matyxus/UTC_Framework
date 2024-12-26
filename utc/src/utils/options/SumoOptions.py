from utc.src.constants.file_system.file_types.sumo_config_file import SumoConfigFile
from utc.src.utils.options.Options import Options
from typing import List, Dict
from sumolib import checkBinary


class SumoOptions(Options):
    """
    Class representing options for traci (sumo) options, provides
    functions to specify which should be used.
    """
    def __init__(self, config_file: SumoConfigFile, display: bool = False, options: Dict[str, str] = None):
        """
        :param config_file: used by sumo
        :param display: if simulation should be run with GUI or not (default False)
        :param options:
        """
        super().__init__(self.set_display(display))
        self.set_input_switch("-c")
        self.config_file: SumoConfigFile = config_file
        self.process_options(options)

    def create_command(self, input_file: str = "", output_file: str = "") -> List[str]:
        """
        :param input_file:
        :param output_file:
        :return:
        """
        return super().create_command(self.config_file.file_path).split()

    # ---------------------------------------------------- Options ----------------------------------------------------

    def add_statistics(self, statistic_file: str):
        """
        :param statistic_file: path to statistic file
        :return: None
        """
        # "--tripinfo-output", "tripinfo.xml",
        # "--summary", "summary.txt"
        self.options += f" --duration-log.statistics true --statistic-output {statistic_file}"

    def set_start_time(self, start_time: int):
        """
        :param start_time: of simulation
        :return: None
        """
        if start_time == -1:
            start_time = self.config_file.get_start_time()
        elif start_time < 0 or start_time > self.config_file.get_end_time():
            print(f"Got invalid start time: {start_time}, setting to simulation start!")
            return
        self.options += f" -b {start_time}"

    def set_end_time(self, end_time: int):
        """
        :param end_time: of simulation
        :return: None
        """
        if end_time > self.config_file.get_end_time() or end_time < self.config_file.get_start_time():
            print(f"Got invalid end time: {end_time}!")
            return
        self.options += f" -e {end_time}"

    def set_step_length(self, step_length: int):
        """
        :param step_length:
        :return:
        """
        self.options += f" --step-length {step_length}"

    def set_display(self, display: bool) -> str:
        """
        :param display: true if simulation should be shown in SumoGui, false otherwise
        :return: Command name
        """
        self.command_name = checkBinary("sumo-gui") if display else checkBinary("sumo")
        return self.command_name

