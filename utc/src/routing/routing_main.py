from utc.src.constants.dynamic.arguments import get_args
from utc.src.constants.file_system.file_types.json_file import JsonFile, FileExtension
from utc.src.routing.pddl.info.pddl_info import PddlInfo
from utc.src.routing.pddl.pddl_episode import PddlEpisode
from utc.src.routing.pddl.pddl_options import PddlOptions, asdict
from utc.src.routing.planning import Mode, Offline, Online
from typing import Optional, List


class PddlMain:
    """
    Class handling routing vehicles by Automated Planning
    """
    def __init__(self, options: PddlOptions):
        """
        :param options: of planning
        """
        assert(options is not None)
        self.options: PddlOptions = options
        self.mode: Optional[Mode] = None
        self.episodes_info: PddlInfo = PddlInfo()
        self._initialized: bool = False

    def run(self) -> bool:
        """
        Runs the planning process based on the given options

        :return: True on success, false otherwise
        """
        # Initialize planning mode
        if self.options.init.mode == "offline":
            self.mode = Offline(self.options)
        else:
            self.mode = Online(self.options)
        # Run the planning
        episodes: List[PddlEpisode] = self.mode.generate_episodes()
        if episodes is None or not episodes:
            print("Error occurred while generating episodes!")
            return False
        # Aggregate information from episodes and save it
        for episode in episodes:
            self.episodes_info.add_record(episode.info)
        self.episodes_info.save(self.mode.new_scenario.name)
        # Save the newly created routes along with vehicles
        if not self.mode.new_scenario.save(self.mode.scenario.config_file.get_network(), False):
            return False
        # Finally save config to given scenario
        config_path: str = self.mode.new_scenario.scenario_dir.info.format_file("config" + FileExtension.JSON)
        return JsonFile(config_path).save(config_path, asdict(self.options))


if __name__ == '__main__':
    config: dict = JsonFile.load_config(get_args().get("config"))
    if not config or config is None:
        raise ValueError("Received invalid config!")
    pddl_main: PddlMain = PddlMain(PddlOptions.dataclass_from_dict(PddlOptions, config))
    pddl_main.run()
