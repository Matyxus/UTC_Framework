import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class VehicleInfo:
    """ Class holding information about vehicles during routing process """
    total: int = 0          # Total number of vehicles considered for planning
    scheduled: int = 0      # Total number of vehicles scheduled for planning
    routed: int = 0         # How many vehicles were routed by planner
    short_route: int = 0    # How many were discarded because of short route (<3 edges)
    invalid_route: int = 0  # No route found (self loop), or only 1 route found

    def __add__(self, other: 'VehicleInfo') -> 'VehicleInfo':
        """
        :param other: vehicle info class
        :return: 'self' with added values from 'other'
        """
        self.total += other.total
        self.scheduled += other.scheduled
        self.routed += other.routed
        self.short_route += other.short_route
        self.invalid_route += other.invalid_route
        return self


@dataclass
class ProblemInfo:
    """ Class holding information about pddl problem during routing process """
    name: str           # Name of pddl problem file
    time: float         # Time taken (seconds) to generate & save problem file to disk (3 digit precision)
    routes: int = 0     # Total number of routes (in the network)
    junctions: int = 0  # Total number of junctions (in the network, does not account for splitting)

    def __init__(self, name: str):
        """
        :param name: name of the pddl problem
        """
        self.name = name
        self.time = time.time()

    def problem_finished(self) -> None:
        """
        Marks the time it took for problem to finish

        :return: None
        """
        self.time = round(time.time() - self.time, 3)

    def __add__(self, other: 'ProblemInfo') -> 'ProblemInfo':
        """
        :param other: problem info class
        :return: 'self' with added values from 'other'
        """
        self.time += other.time
        self.routes += other.routes
        self.junctions += other.junctions
        return self


@dataclass
class ResultInfo:
    """ Class holding information about pddl result during routing process """
    name: str             # Name of pddl result file
    cost: int = 0         # Plan cost
    plans: int = 0        # How many plan files were generated for this problem
    timeout: float = 0.0  # How much time did planner have ? (3 digit precision)

    def __add__(self, other: 'ResultInfo') -> 'ResultInfo':
        """
        :param other: result info class
        :return: 'self' with added values from 'other'
        """
        self.cost += other.cost
        self.plans += other.plans
        self.timeout += other.timeout
        return self


class EpisodeInfo:
    """
    Class representing information of entire pddl episode, combining pddl problem,
    result and vehicle status into single class.
    """
    def __init__(
            self, identifier: int, vehicle_info: VehicleInfo,
            problem_info: ProblemInfo, result_info: Optional[ResultInfo] = None
        ):
        """
        :param identifier: of PDDL episode (number)
        :param vehicle_info: information about vehicles
        :param problem_info: information about pddl problem
        :param result_info information about pddl result (can be None if it was not generated)
        """
        self.id: int = identifier
        self.vehicle_info: VehicleInfo = vehicle_info
        self.problem_info: ProblemInfo = problem_info
        self.result_info: Optional[ResultInfo] = result_info

    def is_valid(self) -> bool:
        """
        :return:
        """
        return self.id >= 0 and self.result_info is not None

    def to_dict(self) -> dict:
        """
        :return: dictionary representation of pddl episode info
        """
        return {
            f"e{self.id}": {
                "problem": asdict(self.problem_info),
                "vehicle": asdict(self.vehicle_info),
                "result": None if self.result_info is None else asdict(self.result_info)
            }
        }

    def __add__(self, other: 'EpisodeInfo') -> 'EpisodeInfo':
        """
        :param other: episode info class
        :return: self with values added from other episode
        """
        assert(self.is_valid() and other.is_valid())
        self.vehicle_info += other.vehicle_info
        self.problem_info += other.problem_info
        if self.is_valid() and other.is_valid():
            self.result_info += other.result_info
        return self


