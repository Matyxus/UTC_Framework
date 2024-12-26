from utc.src.constants.static.file_constants import DirPaths
from typing import Dict, Tuple

# ---------------------------------- Extension ----------------------------------


class NetworkCapacity:
    """ """
    CAR_LENGTH: float = 4.5  # Average car length (in meters)
    MIN_GAP: float = 2.5  # Minimal gap (meters) between vehicles, as defined in SUMO
    # ------------------- Capacity -------------------
    # Light traffic -> from 0 to 35% of capacity
    LIGHT_CAPACITY_THRESHOLD: Tuple[float, float] = (0, 0.35)
    # Medium -> from 35% to 75% capacity
    MEDIUM_CAPACITY_THRESHOLD: Tuple[float, float] = (LIGHT_CAPACITY_THRESHOLD[1], 0.75)
    # Heavy -> from 75% to 100%, over 100% == congested
    HEAVY_CAPACITY_THRESHOLD: Tuple[float, float] = (MEDIUM_CAPACITY_THRESHOLD[1], 1)
    CAPACITY_THRESHOLDS: list = [LIGHT_CAPACITY_THRESHOLD, MEDIUM_CAPACITY_THRESHOLD, HEAVY_CAPACITY_THRESHOLD]
    # ------------------- Multiplier -------------------
    # Penalization multipliers for higher than light capacity
    LIGHT_CAPACITY_MULTIPLIER: float = 1
    MEDIUM_CAPACITY_MULTIPLIER: float = 10
    HEAVY_CAPACITY_MULTIPLIER: float = 100

    @staticmethod
    def calculate_threshold(capacity: int) -> Dict[str, int]:
        """
        :param capacity: of road
        :return: Mapping of traffic density to number of cars
        """
        assert(capacity > 0)
        ret_val: Dict[str, int] = {"light": 0, "medium": 0, "heavy": 0}
        # Calculate the thresholds
        for threshold_name, threshold in zip(ret_val.keys(), NetworkCapacity.CAPACITY_THRESHOLDS):
            ret_val[threshold_name] = int(capacity * (threshold[1] - threshold[0]))
        # At least one car has to be on the road, before we transition to higher capacity
        ret_val["light"] = max(ret_val["light"], 1)
        # Check values
        if capacity - ret_val["light"] <= 0:
            ret_val["medium"] = 0
            ret_val["heavy"] = 0
        elif capacity - (ret_val["light"] + ret_val["medium"]) <= 0:
            ret_val["heavy"] = 0
        # Add the rest of capacity into "heavy"
        elif sum(list(ret_val.values())) != capacity:
            ret_val["heavy"] += (capacity - sum(list(ret_val.values())))
        # print(f"Capacity: {capacity}, {ret_val}")
        assert (sum(list(ret_val.values())) == capacity)
        return ret_val


# ---------------------------------- Planners ----------------------------------

class PLANNERS:
    """
    Class defining planner calls as format string (expected
    arguments are "domain_file.pddl" "problem_file.pddl" "result_file.pddl")
    """
    MERCURY: str = (DirPaths.PDDL_PLANNERS.format("Mercury/plan-utc") + " {0} {1} {2}")

    @staticmethod
    def get_planner(planner_name: str) -> str:
        """
        Expecting the input of planner to be domain file, problem file, result file (name)

        :param planner_name: name of planner
        :return: format string for shell/cmd command of planner, empty if planner does not exist
        """
        planer: str = getattr(PLANNERS, planner_name.upper(), "")
        if not planer:
            print(f"Planner: {planner_name} is not defined in PLANNERS!")
        return planer
