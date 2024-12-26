from utc.src.routing.planning.mode import Mode, PddlOptions
from utc.src.routing.pddl.pddl_episode import PddlEpisode, PddlProblem, PddlResult
from utc.src.utils.vehicle_extractor import VehicleExtractor, VehicleEntry
import time
from typing import Optional, List, Tuple, Iterator


class Offline(Mode):
    """ Class representing 'offline' mode of planning """
    def __init__(self, options: PddlOptions):
        super().__init__(options)
        self.vehicle_extractor: VehicleExtractor = VehicleExtractor(
            self.scenario.vehicles_file, self.scenario.routes_file
        )

    def generate_episodes(self) -> Optional[List[PddlEpisode]]:
        episodes: List[PddlEpisode] = []
        # First generate all pddl problems
        now: float = time.time()
        it: Optional[Iterator[PddlProblem]] = self.generate_problems()
        if it is None:
            return None
        problems: List[PddlProblem] = [problem for problem in it]
        self.problem_generator = None  # Free memory of problem generator
        print(f"Generated: {len(problems)} problems in: {round(time.time() - now, 3)} sec.")
        # From generate problem files, generate results
        results: List[Optional[PddlResult]] = self.result_generator.generate_results(
            problems, self.options.planning.domain,
            self.options.planning.planner,
            self.new_scenario.scenario_dir,
            self.options.planning.timeout,
            self.options.cpu.processes
        )
        if not results:
            print("Error while generating pddl results!")
            return None
        assert(len(problems) == len(results))
        # Generate pddl episodes classes
        print("Generating episodes and saving results")
        for i, (problem, result) in enumerate(zip(problems, results)):
            episodes.append(PddlEpisode(i, problem, result))
            assert(self.save_result(episodes[-1], free_mem=True))
        return episodes

    def generate_problems(self) -> Optional[Iterator[PddlProblem]]:
        """
        :return: generator of PddlProblem classes, None if error curred
        """
        epi_count, start_time = self.compute_time()
        if epi_count <= 0 or start_time < 0:
            print("Error, starting time and ending time of simulation are invalid!")
            return None
        window: int = self.options.planning.window
        for i in range(1, epi_count+1):
            print(f"***" * 15)
            print(f"Generating pddl problem: {i}/{epi_count}")
            # Get vehicles from vehicle file
            entry: VehicleEntry = self.vehicle_extractor.estimate_arrival_naive(
                (start_time, start_time+self.options.planning.window)
            )
            if entry is None or not entry.vehicles:
                print(f"Unable to extract vehicles in interval: {start_time, start_time + window}")
            else:
                problem: Optional[PddlProblem] = self.problem_generator.generate_problem(
                    entry, f"problem_{start_time}_{start_time + window}", self.options.planning.domain
                )
                if problem is not None:
                    yield problem
            start_time += window
            print(f"Finished pddl problem: {i}/{epi_count}")

    # ----------------------------------- Utils -----------------------------------

    def compute_time(self) -> Tuple[int, int]:
        """
        :return: Total number of episodes, start time
        """
        simulation_length: float = (
            min(self.scenario.vehicles_file.get_end_time(), self.scenario.config_file.get_end_time()) -
            max(self.scenario.vehicles_file.get_start_time(), self.scenario.config_file.get_start_time())
        )
        # print(f"Simulation length: {simulation_length}")
        # We must add one to episodes, since this works as rounding up
        epi_count: int = round(simulation_length / self.options.planning.window) + 1
        start_time: int = int(max(self.scenario.vehicles_file.get_start_time(), self.scenario.config_file.get_start_time()))
        return epi_count, start_time

