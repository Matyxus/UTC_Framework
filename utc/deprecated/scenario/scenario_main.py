from utc.deprecated.ui import UserInterface, Command
from utc.src.constants.file_system import MyFile, MyDirectory, SumoConfigFile
from utc.src.constants.static import FilePaths, DirPaths
from utc.src.simulator.scenario import ScenarioGenerator
from typing import List, Optional
import traci


class ScenarioMain(UserInterface):
    """ Class that ask user for input related to generating SUMO scenarios, generating and running scenarios """

    def __init__(self, log_commands: bool = True):
        super().__init__("scenario", log_commands)
        self.scenario_generator: Optional[ScenarioGenerator] = None

    # ---------------------------------- Commands ----------------------------------

    def initialize_commands(self) -> None:
        super().initialize_commands()
        self.user_input.add_command([
            Command("generate_scenario", self.generate_scenario_command),
            Command("launch_scenario", self.launch_scenario_command)
        ])

    @UserInterface.log_command
    def generate_scenario_command(self, scenario_name: str, network_name: str) -> None:
        """
        Initializes the process of creating new scenario, enables
        new commands to add vehicles to scenario and command to save it

        :param scenario_name: name of scenario (will be used as namespace
        for other files related to scenario, e.g.: pddl files, routes, ..)
        :param network_name: name of network on which simulation will be displayed
        :return: None
        """
        if not MyFile.file_exists(FilePaths.MAP_SUMO.format(network_name)):
            return
        elif MyDirectory.dir_exist(DirPaths.SCENARIO.format(scenario_name), message=False):
            print(
                f"Scenario named: {scenario_name} already exists in:"
                f" {DirPaths.SCENARIO.format(scenario_name)}, choose different name!"
            )
            return
        # Scenario
        self.scenario_generator = ScenarioGenerator(scenario_name, network_name)
        # Add vehicle flow methods to logging
        if self.logging_enabled:
            for cls, methods in self.scenario_generator.vehicle_factory.get_methods():
                self.set_logger(cls, list(methods.values()))
        # Add new commands for user input
        if self.user_input is not None:
            # Add new commands
            # ! flows needs to be added separately from logging loop (new pointers) !
            for cls, methods in self.scenario_generator.vehicle_factory.get_methods():
                self.user_input.add_command([
                    Command(command_name, method) for command_name, method in methods.items()
                ])
            self.user_input.add_command([
                Command("save_scenario", self.save_scenario_command),
                Command("plot", self.scenario_generator.graph.display.plot)
            ])

    # noinspection PyMethodMayBeStatic
    def launch_scenario_command(
            self, scenario_name: str, statistics: bool = True,
            display: bool = True, traffic_lights: bool = True
            ) -> None:
        """
        :param scenario_name: name of existing scenario (can be user-generated or planned)
        :param statistics: bool, if file containing vehicle statistics should be generated (default true)
        :param display: bool, if simulation should be launched with GUI (default true)
        :param traffic_lights: bool, fi simulation should use traffic lights (default true)
        :return: None
        """
        # Get scenario path (can be planned or user-generated)
        scenario_path: str = SumoConfigFile(scenario_name).file_path
        if not MyFile.file_exists(scenario_path, message=False):
            print(f"Scenario named: {scenario_name} does not exist!")
            return
        traci_options: TraciOptions = TraciOptions()
        options: List[str] = traci_options.get_options(scenario_path)
        if statistics:
            options += traci_options.get_statistics(scenario_name)
        try:
            traci.start([traci_options.get_display(display), *options])
            # Turn of traffic lights
            if not traffic_lights:
                for traffic_light_id in traci.trafficlight.getIDList():
                    traci.trafficlight.setProgram(traffic_light_id, "off")
            # Main loop
            while traci.simulation.getMinExpectedNumber() > 0:  # -> "while running.."
                traci.simulationStep()
            traci.close()
            print(f"Simulation of scenario: '{scenario_name}' ended, exiting ...")
        except traci.exceptions.FatalTraCIError as e:
            # Closed by user
            if str(e) == "connection closed by SUMO":
                print("Closed GUI, exiting ....")
            else:
                print(f"Error occurred: {e}")

    @UserInterface.log_command
    def save_scenario_command(self) -> None:
        """
        Saves scenario -> '.sucmofg' (executable) file and
        '.rou.xml' file (containing vehicles and their routes),
        saves logged commands (if enabled) and
        removes all commands except initial ones

        :return: None
        """
        # Save scenario
        if self.scenario_generator.save():
            # Save info file
            if self.logging_enabled:
                self.save_log(
                    FilePaths.SCENARIO_INFO.format(
                        self.scenario_generator.scenario.name,
                        self.scenario_generator.scenario.name
                    )
                )
        self.clear_log()
        # Reset
        self.scenario_generator = None
        if self.user_input is not None:
            # Remove commands enabled only after generating scenario
            self.user_input.remove_command(
                list(self.user_input.commands.keys() ^ {
                    "generate_scenario", "launch_scenario", "delete_scenario", "help", "exit"
                })
            )


if __name__ == "__main__":
    scenario_launcher: ScenarioMain = ScenarioMain()
    scenario_launcher.run()
