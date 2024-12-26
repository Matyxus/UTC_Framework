import unittest
from utc.src.utils.constants import PATH, PLANNERS, dir_exist
from os import mkdir
from typing import List


class StructureTest(unittest.TestCase):
    """ Test structure of project """

    def test_path(self) -> None:
        """
        Tests structure of project, mainly folders and PATH, PLANNER classes

        :return: None
        """
        if not PATH.CWD.endswith("utc"):
            raise ValueError(f"Variable of class PATH: CWD = {PATH.CWD} must point to '../UTC/utc'!")
        # /utc/data
        self.check_dir(PATH.CWD + "/data")

    def test_scenarios(self) -> None:
        """
        Tests scenario folder in /Utc/utc/data

        :return:
        """
        if not PATH.CWD.endswith("utc"):
            raise ValueError(f"Variable of class PATH: CWD = {PATH.CWD} must point to '../UTC/utc'!")
        scenario_dir: str = PATH.CWD + "/data/scenarios"
        dirs_to_check: List[str] = [
            scenario_dir, scenario_dir + "/problems",
            scenario_dir + "/results", scenario_dir + "/routes",
            scenario_dir + "/simulation", scenario_dir + "/statistics"
        ]
        for directory in dirs_to_check:
            self.check_dir(directory)

    def test_maps(self) -> None:
        """
        Tests maps folder in /Utc/utc/data

        :return:
        """
        if not PATH.CWD.endswith("utc"):
            raise ValueError(f"Variable of class PATH: CWD = {PATH.CWD} must point to '../UTC/utc'!")
        maps_dir: str = PATH.CWD + "/data/maps"
        dirs_to_check: List[str] = [
            maps_dir, maps_dir + "/osm",
            maps_dir + "/osm/original", maps_dir + "/osm/filtered",
            maps_dir + "/sumo"
        ]
        for directory in dirs_to_check:
            self.check_dir(directory)

    def check_dir(self, dir_path: str) -> None:
        """
        Checks if directory exists, if not, it will be created

        :param dir_path: to check
        :return: None
        """
        if not dir_exist(dir_path, message=False):
            print(f"Unable to find directory: {dir_path}, creating ...")
            mkdir(dir_path)
            assert (dir_exist(dir_path, message=False))



