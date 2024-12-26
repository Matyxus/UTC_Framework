from utc.src.semestral.evolutionary.algorithm import Algorithm, Population
from utc.src.semestral.evolutionary.operators import OPERATORS
from copy import deepcopy
from numpy import exp, random
from typing import Optional, List


class SimulatedAnnealing(Algorithm):
    """
    Classical implementation of SimulatedAnnealing algorithm: https://en.wikipedia.org/wiki/Simulated_annealing,
    with both parameters 'temperature' and 'cooling_rate'. Performs minimization of waiting time as metric.
    """
    def __init__(self, params: dict):
        """
        :param params: parameters of algorithm
        """
        super().__init__("SimulatedAnnealing", params)

    def step(self, iteration: int) -> Optional[Population]:
        if not self.is_running():
            print(f"Error, algorithm: {self.name} is not running!")
            return None
        # Generate new solution (always perform mutation)
        new_solution: Population = deepcopy(self.population)
        new_solution.mutate(self.params["mutation_chance"], OPERATORS["mutation"][self.params["mutation"]])
        assert(self.evaluate_population(new_solution))
        # SimulatedAnnealing only optimizes waiting time
        if self.accept_solution(self.population.fitness[0], new_solution.fitness[0]) > random.rand():
            self.population = new_solution
        self.params["temperature"] *= (1.0 - self.params["cooling_rate"])
        return self.population

    def accept_solution(self, current_energy: float, new_energy: float) -> float:
        """
        :param current_energy: current fitness
        :param new_energy:  new fitness
        :return: The probability of accepting solution (by exponential formula)
        """
        # Found better solution
        if new_energy < current_energy:
            return 1.0
        return exp((current_energy - new_energy) / self.params["temperature"])

    def init_population(self, phases: int, size: int) -> bool:
        """
        :param phases: number of phases each TL has
        :param size: number of TLs in simulation
        :return: True on success, false otherwise
        """
        print(f"Initializing population phases: {phases}, size: {size}")
        self.population = Population(OPERATORS["initialization"][self.params["initialization"]](phases, size))
        return self.evaluate_population(self.population)

    # ------------------------------------- Utils -------------------------------------

    def check_params(self) -> bool:
        keys: List[str] = ["cooling_rate", "temperature"]
        for key in keys:
            # Check existence
            if key not in self.params:
                print(f"Missing parameter: {key} !")
                return False
        # Check type and value
        if not (isinstance(self.params["cooling_rate"], float) and 0 < self.params["cooling_rate"] < 1):
            print(f"Expected parameter cooling_rate to be number in range (0, 1), got: {self.params['cooling_rate']}")
            return False
        elif not (isinstance(self.params["temperature"], (float, int)) and self.params["temperature"] > 1):
            print(f"Expected parameter temperature to be number > 1, got: {self.params['temperature']}")
            return False
        elif self.params["mutation_chance"] < 0.1:
            print(f"Mutation in SimulatedAnnealing has to be at least 10%, as it is applied individually, changing ..")
            self.params["mutation_chance"] = 0.1
        return True

    def is_running(self) -> bool:
        return self.params["temperature"] > 1 and self.population is not None

