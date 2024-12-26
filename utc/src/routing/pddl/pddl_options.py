from utc.src.constants.options.options import Options
from utc.src.constants.options.logging_options import LoggingOptions
from utc.src.constants.options.misc_options import CpuOptions, InfoOptions
from utc.src.constants.options.network_options import NetworkOptions
from dataclasses import dataclass, asdict


@dataclass
class PddlInitOptions(Options):
    """ Data class for planning initialization """
    scenario: str
    new_scenario: str
    network: str
    mode: str = "offline"
    snapshot: str = None

    def validate_options(self) -> bool:
        return self.validate_data(asdict(self), "PddlInitOptions")


@dataclass
class PddlPlanningOptions(Options):
    """ Data class for planning """
    window: int = 30
    timeout: float = 27
    planner: str = "Mercury"
    domain: str = "utc_allowed"
    keep_problems: bool = True
    keep_results: bool = True
    keep_planner_output: bool = False

    def validate_options(self) -> bool:
        return self.validate_data(asdict(self), "PddlPlanningOptions")


@dataclass
class PddlOptions(Options):
    """ Data class for vehicle routing """
    # Misc
    info: InfoOptions = None
    logs: LoggingOptions = None
    cpu: CpuOptions = None
    # Main
    init: PddlInitOptions = None
    planning: PddlPlanningOptions = None
    network: NetworkOptions = None

    def validate_options(self) -> bool:
        return None not in (self.info, self.logs, self.cpu, self.init, self.planning, self.network)


# For testing purposes
if __name__ == '__main__':
    from json import load
    from utc.src.constants.static.file_constants import FilePaths
    file_path: str = FilePaths.CONFIG_FILE.format("pddl_config")
    with open(file_path, "r") as json_file:
        data = load(json_file)
    pddl_options: PddlOptions = Options.dataclass_from_dict(PddlOptions, data)
