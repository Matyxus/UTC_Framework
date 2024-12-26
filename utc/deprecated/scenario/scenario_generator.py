from utc.src.simulator.scenario.scenario import Scenario
from utc.src.constants.file_system import MyDirectory
from utc.src.constants.static import DirPaths
from utc.src.simulator.vehicle import VehicleFactory
from utc.src.graph.network.components import RoadNetwork
from utc.src.graph import Graph
from typing import Optional


class ScenarioGenerator:
    """
    Class generating default scenarios (not planned with planners),
    generates scenario directory, with default scenario ('.sumocfg' and '.rou.xml' files),
    only new scenario namespace can be created using this class
    """

    def __init__(self, scenario: str, network: str):
        """
        :param scenario: name of scenario, will be used for files corresponding
        to scenario e.g. ".sumocfg", ".rou.xml", etc.
        :param network: name of road network file on which simulation will be displayed
        """
        self.scenario: Scenario = Scenario(scenario, scenario_folder=scenario, create_new=True)
        self.graph: Optional[Graph] = None
        self.vehicle_factory: Optional[VehicleFactory] = None
        self.load(scenario, network)

    def load(self, scenario: str, network: str) -> None:
        """
        :param scenario: name of scenario to load, if such name does not exist, new directory
        will be created when saving scenario
        :param network: name of road network file on which simulation will be displayed,
        if default, network will be extracted from existing scenario.sumocfg file
        :return: None

        :raises FileNotFoundError: if network does not exist
        :raises ValueError: if scenario does not exist and network == 'default' or
        if error occurred during loading ".sumocfg" or ".rou.xml" file
        :raises ValueError: if scenario exits, only new can be created using this class
        """
        # Check existence
        if MyDirectory.dir_exist(DirPaths.SCENARIO.format(scenario), message=False):
            raise ValueError(
                f"Error scenario folder named: '{scenario}' already"
                f" exists! Can only create new scenarios using 'ScenarioGenerator'"
            )
        # Graph
        self.graph: Graph = Graph(RoadNetwork())
        if not self.graph.loader.load_map(network):
            raise FileNotFoundError(f"Error at loading network: '{network}'!")
        self.graph.simplify.simplify_graph()
        # Vehicle generator
        self.vehicle_factory = VehicleFactory(self.graph)

    def save(self) -> bool:
        """
        Creates scenario class with default scenario directory and associated files.

        :return: True on success, false otherwise
        """
        if MyDirectory.dir_exist(DirPaths.SCENARIO.format(self.scenario.name), message=False):
            print(f"Cannot create scenario and folder: {self.scenario.name}, they already exist!")
            return False
        print(f"Creating scenario: {self.scenario.name} and folder: {self.scenario.name}")
        # Add vehicles to routes file
        if self.vehicle_factory is not None:
            self.vehicle_factory.save(self.scenario.routes_file.root)
        self.scenario.config_file.set_routes_file(self.scenario.name)
        self.scenario.config_file.set_network_name(self.graph.road_network.map_name, False)
        success: bool = self.scenario.save(with_directory=True)
        print(f"Scenario namespace: '{self.scenario.name}' created successfully: '{success}'")
        return success


# For testing purposes
if __name__ == "__main__":
    temp: Scenario = Scenario("test", "Chodov")


