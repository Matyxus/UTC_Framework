from utc.src.semestral.evolutionary.algorithm import Algorithm, Population
from utc.src.semestral.evolutionary.operators import OPERATORS
from numpy import random
from typing import Optional, List


class NSGA2(Algorithm):
    """
    Classical implementation of NSGA2, including fast domination sorting and crowding distance assignment
    """
    def __init__(self, params: dict):
        """
        :param params: parameters of algorithm
        """
        super().__init__("NSGA2", params)

    def step(self, iteration: int) -> Optional[List[Population]]:
        if not self.is_running():
            print(f"Error, algorithm: {self.name} is not running!")
            return None
        # ---------- Selection + Cross over + Mutation + Fitness ----------
        indexes: List[int] = OPERATORS["selection"]["rank_binary_tournament"](
            self.population, self.params["population"]
        )
        new_population: List[Population] = []
        for _ in range(0, len(indexes), 2):
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
        # Evaluate new population + domination sort
        self.evaluate_population(new_population)
        self.population += new_population
        self.domination_sort(self.population)
        # Set crowding distance only to solution, which will be picked in the next generation
        start: int = 1
        for rank in range(self.population[0].rank, self.population[self.params["population"] - 1].rank):
            end: int = start
            # Find the all the pops of this rank
            while end < len(self.population) and self.population[end].rank == rank:
                end += 1
            # Do not compute crowding distance for single or 2 elements of the same rank
            if end <= start + 2:
                start = end
                continue
            self.compute_crowding_distance(self.population[start:end])
            start = end
        # Sort the last set, if it is unclear (based on rank) what will be taken into new population
        start: int = self.params["population"] - 1
        if self.population[start].rank == self.population[start+1].rank:
            end: int = start + 1
            rank: int = self.population[start].rank
            while start >= 0 and self.population[start].rank == rank:
                start -= 1
            while end < len(self.population) and self.population[end].rank == rank:
                end += 1
            start += 1
            end -= (end == self.population)
            self.population[start:end] = sorted(self.population[start:end], key=lambda x: x.crowding_dist, reverse=True)
        # Replacement strategy
        self.population = self.population[0:self.params["population"]]
        return list(filter(lambda x: x.rank == 1, self.population))

    def domination_sort(self, population: List[Population]) -> None:
        """
        :param population: which will be sorted (in-place) by domination
        :return: None
        """
        size: int = len(population)
        # Domination fronts of each individual (other individual dominated by the current one), in index form
        fronts: List[List[int]] = [[] for _ in range(size)]
        dom_count: List[int] = [0] * size
        for i in range(size):
            # Check who solution dominates / is dominated by
            for j in range(i+1, size):
                # "i" dominates "j"
                if population[i].dominates(population[j]):
                    fronts[i].append(j)
                    dom_count[j] += 1
                # "j" dominates "i"
                elif population[j].dominates(population[i]):
                    fronts[j].append(i)
                    dom_count[i] += 1
            # Solution is not dominated by any other,
            # Also works as reset of rank for previous population (i.e. when it is direct copy)
            population[i].rank = (dom_count[i] == 0)
            # Reset crowding distance
            population[i].crowding_dist = 0
        # Compute ranks
        rank: int = 1  # Current rank we are searching for
        changed_rank: bool = True
        while changed_rank:
            changed_rank = False
            for i in range(size):
                # Found solution with current rank, remove it from search
                if population[i].rank == rank:
                    changed_rank = True
                    for j in fronts[i]:
                        dom_count[j] -= 1
                        # Assign new rank, if solution is not dominated by any other
                        population[j].rank = (dom_count[j] == 0) * (rank + 1)
            # Update rank
            rank += 1
        # Sort by rank
        return population.sort(key=lambda x: x.rank)

    def compute_crowding_distance(self, population: List[Population]) -> None:
        """
        :param population: over which crowding distance should be computed
        :return: None
        """
        size: int = len(population)
        assert(size != 0)
        assert(all(population[i].fitness is not None for i in range(size)))
        assert(len(set([population[i].rank is not None for i in range(size)])) == 1)
        if size <= 2:
            population[0].crowding_dist = population[-1].crowding_dist = 0
            return
        width: float = 0
        for objective in range(len(population[0].fitness)):
            population.sort(key=lambda x: x.fitness[objective])
            population[0].crowding_dist = population[-1].crowding_dist = float("inf")
            # No need to compute crowding distance, if solutions have the same values
            if population[0].fitness[objective] != population[-1].fitness[objective]:
                width = (population[-1].fitness[objective] - population[0].fitness[objective])
                # Crowding distance is computed for the in-between solutions
                for i in range(1, size-1):
                    population[i].crowding_dist += (
                        (population[i+1].fitness[objective] - population[i-1].fitness[objective]) / width
                    )
        return

    # ------------------------------------- Utils -------------------------------------

    def init_population(self, phases: int, size: int) -> bool:
        """
        :param phases: number of phases each TL has
        :param size: number of TLs in simulation
        :return: True on success, false otherwise
        """
        # Make sure population is odd number
        self.params["population"] += not (self.params["population"] & 1)
        print(f"Initializing population phases: {phases}, size: {size}, pops: {self.params['population']}")
        self.population = [
            Population(OPERATORS["initialization"][self.params["initialization"]](phases, size))
            for _ in range(self.params['population'])
        ]
        # Evaluate
        return self.evaluate_population(self.population)

    # NSGA2 does not implement any special parameters
    def check_params(self) -> bool:
        return True

    def is_running(self) -> bool:
        return self.population is not None



