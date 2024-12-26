from utc.src.semestral.evolutionary.algorithm import Algorithm, Population
from utc.src.semestral.evolutionary.operators import OPERATORS
from numpy import random
from math import ceil
from typing import Optional, List


class GeneticAlgorithm(Algorithm):
    """
    Classical implementation of GeneticAlgorithm, which uses elitism to keep the best performing populations
    """

    def __init__(self, params: dict):
        """
        :param params: parameters of algorithm
        """
        super().__init__("GeneticAlgorithm", params)

    def step(self, iteration: int) -> Optional[Population]:
        if not self.is_running():
            print(f"Error, algorithm: {self.name} is not running!")
            return None
        new_population: List[Population] = []
        # -- Elitism -- (ceil makes sure we at least pick one each time)
        new_population += self.population[0:ceil(self.params["population"] * self.params["elitism"])]
        # ---------- Selection + Cross over + Mutation + Fitness ----------
        # Selection
        indexes: List[int] = OPERATORS["selection"][self.params["selection"]](
            self.population, self.params["population"] - len(new_population)
        )
        # Divide size by 2, as we always pick 2 at once
        for _ in range(ceil(self.params["population"] / 2)):
            i, j = random.choice(indexes, 2)
            # Crossover
            a, b = self.population[i].crossover(
                self.population[j], self.params["crossover_chance"],
                OPERATORS["crossover"][self.params["crossover"]]
            )
            # Mutation
            a.mutate(self.params["mutation_chance"], OPERATORS["mutation"][self.params["mutation"]])
            b.mutate(self.params["mutation_chance"], OPERATORS["mutation"][self.params["mutation"]])
            # Add new solutions
            new_population.append(a)
            new_population.append(b)
        assert (len(new_population) >= self.params["population"])
        new_population = new_population[0:self.params["population"]]
        self.evaluate_population(new_population)
        # Generational replacement, sort and return best
        self.population = sorted(new_population)
        return self.population[0]

    def init_population(self, phases: int, size: int) -> bool:
        """
        :param phases: number of phases each TL has
        :param size: number of TLs in simulation
        :return: True on success, false otherwise
        """
        print(f"Initializing population phases: {phases}, size: {size}, pops: {self.params['population']}")
        self.population = [
            Population(OPERATORS["initialization"][self.params["initialization"]](phases, size))
            for _ in range(self.params['population'])
        ]
        # Evaluate and sort population
        if not self.evaluate_population(self.population):
            return False
        self.population = sorted(self.population)
        return True

    # ------------------------------------- Utils -------------------------------------

    def check_params(self) -> bool:
        # Check existence
        if "elitism" not in self.params:
            print(f"Missing parameter: {'elitism'} !")
            return False
        # Check type and value
        if not (isinstance(self.params["elitism"], float) and 0 < self.params["elitism"] < 1):
            print(f"Expected parameter elitism to be number in range (0, 1), got: {self.params['elitism']}")
            return False
        return True

    def is_running(self) -> bool:
        return self.population is not None



