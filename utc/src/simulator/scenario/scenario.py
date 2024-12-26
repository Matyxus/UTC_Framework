from utc.src.constants.file_system.directory_types import ScenarioDir
from utc.src.constants.file_system.file_types.sumo_config_file import SumoConfigFile, FilePaths
from utc.src.constants.file_system.file_types.sumo_routes_file import SumoRoutesFile
from utc.src.constants.file_system.file_types.sumo_vehicles_file import SumoVehiclesFile
from typing import Optional


class Scenario:
    """
    Class representing scenario, holds associated files/directories:\n
    - *pddl problems & results directory\n
    - *statistics file (SUMO xml statistics, aggregating csv file)\n
    - *information directory (log files, config, etc.)\n
    - additional files (routes - '.rou.xml', vehicle files etc.)\n
    - config directory '.sumocfg'\n
    Items denoted as '*' are optional, all scenarios are located in '/data/scenarios'
    directory (scenario name is used as name space for all its associated files).
    """
    def __init__(self, scenario_name: str, create_new: bool = False):
        """
        :param scenario_name: name of scenario folder
        :param create_new: if new scenario should be created (only non-optional dirs will be created)
        """
        self.name: str = scenario_name
        self.scenario_dir: Optional[ScenarioDir] = None
        # Main files associated with scenarios (can have multiple, but at least these must always be present)
        self.config_file: Optional[SumoConfigFile] = None
        self.routes_file: Optional[SumoRoutesFile] = None
        self.vehicles_file: Optional[SumoVehiclesFile] = None
        self.load(create_new)

    # ------------------------------------------ File ------------------------------------------

    def load(self, create_new: bool = True) -> None:
        """
        :param create_new: if new scenario should be created (loads main files as template files)
        """
        # Associated directories with scenario
        self.scenario_dir = ScenarioDir(self.name)
        # Associated files with scenario
        if create_new:  # Load templates
            self.config_file = SumoConfigFile(FilePaths.XmlTemplates.SUMO_CONFIG)
            self.routes_file = SumoRoutesFile(FilePaths.XmlTemplates.SUMO_ROUTES)
            self.vehicles_file = SumoVehiclesFile(FilePaths.XmlTemplates.SUMO_VEHICLE)
        else:  # Load existing (have to exist)
            self.config_file = SumoConfigFile(FilePaths.SCENARIO_CONFIG.format(self.name, self.name))
            self.routes_file = SumoRoutesFile(FilePaths.SCENARIO_ROUTES.format(self.name, self.name))
            self.vehicles_file = SumoVehiclesFile(FilePaths.SCENARIO_VEHICLES.format(self.name, self.name))

    def save(self, road_network: str, with_directory: bool = True) -> bool:
        """
        Creates '.rou.xml' file containing vehicle types, routes, individual vehicles.
        Creates '.sumocfg' file that launches simulation in SUMO GUI (expecting
        xml element "net-file" and "routes-file" to be set before saving)

        :param road_network: path to road network file to be set for scenario
        :param with_directory: initializes scenario directory
        structure (default one) if true, false by default
        :return: true on success, false otherwise
        """
        print(f"Saving scenario: '{self.name}'")
        # Initialize directory
        if with_directory:
            if self.scenario_dir is None:
                self.scenario_dir = ScenarioDir(self.name)
            if not self.scenario_dir.initialize_dir():
                return False
        # Check
        if None in (self.config_file, self.routes_file, self.vehicles_file):
            print("Either configuration or routes or vehicle files are 'None', cannot create scenario!")
            return False
        # Create "scenario_routes.rou.xml"
        elif not self.routes_file.save(FilePaths.SCENARIO_ROUTES.format(self.name, self.name)):
            return False
        # Create vehicle file
        elif not self.vehicles_file.save(FilePaths.SCENARIO_VEHICLES.format(self.name, self.name)):
            return False
        # Create ".sumocfg" (executable)
        self.config_file.set_network_file(road_network)
        self.config_file.set_routes_file(FilePaths.SCENARIO_ROUTES.format(self.name, self.name))
        self.config_file.set_additional_file(FilePaths.SCENARIO_VEHICLES.format(self.name, self.name))
        if not self.config_file.save(FilePaths.SCENARIO_CONFIG.format(self.name, self.name)):
            return False
        print(f"Scenario: '{self.name}' created successfully")
        return True

    # ------------------------------------------ Utils ------------------------------------------

    def exists(self, message: bool = False) -> bool:
        """
        Scenarios exists, if its folder does exist and associated files,
        routes ('.rou.xml'), config ('.sumocfg'), vehicles ('_vehicles.add.xml')

        :param message: true if message about missing file/folder
        should be printed, default false
        :return: true if scenario exists, false otherwise
        """
        if self.scenario_dir is None or not self.scenario_dir.is_loaded(message):
            return False
        elif self.config_file is None or not self.config_file.is_loaded():
            return False
        elif self.routes_file is None or not self.routes_file.is_loaded():
            return False
        return self.vehicles_file is None or self.vehicles_file.is_loaded()

