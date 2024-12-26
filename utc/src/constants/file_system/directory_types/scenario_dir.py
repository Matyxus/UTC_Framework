from utc.src.constants.file_system.my_directory import MyDirectory
from utc.src.constants.static import DirPaths, FileExtension
from typing import Optional, List


class ScenarioDir(MyDirectory):
    """
    Class representing entire directory of scenario, has 6 sub-directories:\n
    1 - config_dir (representing directory of SUMO config files)\n
    2 - additional_dir (containing route, vehicle and other files)\n
    3 - problems_dir (optional, containing '.pddl' problem directories)\n
    4 - results_dir (optional, containing '.pddl' result directories)\n
    5 - info_dir (optional, containing log file, config used on scenario etc.)\n
    6 - stats_dir (optional, containing SUMO statistics files and/or csv file)\n
    """
    def __init__(self, scenario_name: str):
        """
        :param scenario_name: name of scenario folder (does not have to exist)
        """
        super().__init__(DirPaths.SCENARIO.format(scenario_name))
        self.additional: MyDirectory = MyDirectory(DirPaths.SCENARIO_ADDITIONAL.format(scenario_name))
        self.problems: MyDirectory = MyDirectory(DirPaths.PDDL_PROBLEMS.format(scenario_name))
        self.results: MyDirectory = MyDirectory(DirPaths.PDDL_RESULTS.format(scenario_name))
        self.config: MyDirectory = MyDirectory(DirPaths.SCENARIO_CONFIGS.format(scenario_name))
        self.stats: MyDirectory = MyDirectory(DirPaths.SCENARIO_STATISTICS.format(scenario_name))
        self.info: MyDirectory = MyDirectory(DirPaths.SCENARIO_INFOS.format(scenario_name))

    # -------------------------------------------- Getters --------------------------------------------

    def get_problems(self, full_path: bool = False, extension: bool = False, sort: bool = False) -> Optional[List[str]]:
        """
        :param full_path: if files should contain their full path (False by default)
        :param extension: if files should contain their extension (False by default)
        :param sort: True if files should be sorted (False by default - no sorting - random order)
        :return: List of pddl problem file names, None if error occurred
        """
        if self.problems is None or not self.problems.is_loaded():
            return None
        return self.problems.list_dir(full_path, extension, sort)

    def get_results(self, full_path: bool = False, extension: bool = False, sort: bool = False) -> Optional[List[str]]:
        """
        :param full_path: if files should contain their full path (False by default)
        :param extension: if files should contain their extension (False by default)
        :param sort: True if files should be sorted (False by default - no sorting - random order)
        :return: List of pddl result files names, None if error occurred
        """
        if self.results is None or not self.results.is_loaded():
            return None
        return self.results.list_dir(full_path, extension, sort)

    def get_config(self, name: str = "") -> Optional[str]:
        """
        :param name: of config file (if not given, returns default - same name as scenario)
        :return: Configuration file path, None if error occurred
        """
        if self.config is None or not self.config.is_loaded():
            return None
        return self.config.get_file((self.name if not name else name) + FileExtension.SUMO_CONFIG)

    # -------------------------------------------- Utils --------------------------------------------

    def initialize_dir(self, pddl: bool = False, info_dir: bool = False, stats_dir: bool = False) -> bool:
        """
        Initializes scenario directory structure (only the minimal structure)

        :param pddl: true if pddl directories should be initialized (False by default)
        :param info_dir: true if info directory should be initialized (False by default)
        :param stats_dir: true if stats directory should be initialized (False by default)
        :return: True on success, false otherwise
        """
        if not super().initialize_dir() or not self.additional.initialize_dir() or not self.config.initialize_dir():
            return False
        if pddl and not (self.problems.initialize_dir() and self.results.initialize_dir()):
            return False
        if info_dir and not self.info.initialize_dir():
            return False
        return True if not stats_dir else self.stats.initialize_dir()

