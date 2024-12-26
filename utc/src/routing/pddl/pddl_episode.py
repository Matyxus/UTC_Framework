from utc.src.routing.pddl.info.episode_info import EpisodeInfo
from utc.src.routing.pddl.base.pddl_problem import PddlProblem
from utc.src.routing.pddl.base.pddl_result import PddlResult
from typing import Optional


class PddlEpisode:
    """
    Class modeling episode of pddl planning task, contains both pddl problem and result classes,
    along with additional information and utility methods.
    """
    def __init__(self, identifier: int, problem: PddlProblem, result: Optional[PddlResult] = None):
        """
        :param identifier: identifier of episode (i.e. what number it is)
        :param problem: Pddl Problem class representing pddl problem file
        :param result: Pddl Result class representing all result files corresponding to the given problem
        """
        self.id: int = identifier
        self.problem: PddlProblem = problem  # Class modeling pddl problem
        self.result: Optional[PddlResult] = result  # Class modeling pddl result (can be 'None')
        self.info: EpisodeInfo = EpisodeInfo(
            identifier, self.problem.container.info,
            self.problem.info, None if self.result is None else self.result.info
        )  # Info about the episode (i.e. the problem and result)

    def is_valid(self) -> bool:
        """
        :return: True if pddl episode is valid (i.e. everything is initialized), False otherwise
        """
        return None not in (self.info, self.problem, self.result)

    def free_mem(self) -> None:
        """
        Frees memory of episode, i.e. the network of pddl problem, vehicles, etc.

        :return: None
        """
        self.problem.network = None
        self.problem.container.vehicles.clear()
        self.problem.container.vehicle_abstraction.clear()
        if self.result is not None:
            self.result.files.clear()
        return
