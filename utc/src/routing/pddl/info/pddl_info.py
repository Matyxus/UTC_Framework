from utc.src.constants.static import DirPaths, FilePaths
from utc.src.constants.file_system.my_directory import MyDirectory
from utc.src.constants.file_system.file_types.json_file import JsonFile
from utc.src.routing.pddl.info.episode_info import EpisodeInfo, VehicleInfo, ResultInfo, ProblemInfo, asdict
from typing import List


class PddlInfo:
    """ Class storing information about all planning episodes, includes total and average comparison """
    def __init__(self):
        self.history: List[EpisodeInfo] = []

    def add_record(self, info: EpisodeInfo) -> None:
        """
        :param info: information about pddl episode
        :return: None
        """
        self.history.append(info)

    def additional_info(self) -> dict:
        """
        :return: Dictionary containing total & average info of all episodes (aggregated together)
        """
        # Aggregate values
        episodes: int = len(self.history)
        problems_dict: dict = {"total": episodes}
        results_dict: dict = {"unique": 0}
        vehicles_info: VehicleInfo = VehicleInfo()
        results_info: ResultInfo = ResultInfo("")
        problems_info: ProblemInfo = ProblemInfo("")
        problems_info.time = 0.0
        for episode_info in self.history:
            vehicles_info += episode_info.vehicle_info
            problems_info += episode_info.problem_info
            if episode_info.result_info is not None:
                results_info += episode_info.result_info
                results_dict["unique"] += (episode_info.result_info.plans > 0)
        # Construct the dictionary
        problems_dict |= asdict(problems_info)
        results_dict |= asdict(results_info)
        problems_dict.pop("name")
        results_dict.pop("name")
        total_info: dict = {
            "total": {
                "problems": problems_dict,
                "results":  results_dict,
                "vehicles": asdict(vehicles_info)
            },
            "average": {
                "problems": {k: round(v / episodes, 2) for k, v in problems_dict.items() if not isinstance(v, str)},
                "results":  {k: round(v / episodes, 2) for k, v in results_dict.items() if not isinstance(v, str)},
                "vehicles": {k: round(v / episodes, 2) for k, v in asdict(vehicles_info).items()}
            }
        }
        return total_info

    def save(self, scenario_name: str, file_name: str = "default") -> bool:
        """
        :param scenario_name: Name of pddl scenario directory
        :param file_name: If 'default' uses '[scenario_name]_pddl_info' as file name
        :return: True on success, false otherwise
        """
        file_name = (f"{scenario_name}_pddl_info" if (not file_name or file_name == "default") else file_name)
        if not MyDirectory.dir_exist(DirPaths.SCENARIO.format(scenario_name)):
            return False
        elif not MyDirectory.make_directory(DirPaths.SCENARIO_INFOS.format(scenario_name)):
            return False
        elif not self.history:
            print("Empty history of episodes, cannot generate info file!")
            return False
        # Save data to file
        json_file: JsonFile = JsonFile(FilePaths.SCENARIO_INFO.format(scenario_name, file_name))
        data: dict = self.additional_info()
        for episode_info in self.history:
            data |= episode_info.to_dict()
        return json_file.save(data=data)

