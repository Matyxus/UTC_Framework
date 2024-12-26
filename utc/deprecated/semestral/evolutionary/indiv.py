from utc.src.semestral.tl_constants import MIN_GREEN_TIME, MAX_GREEN_TIME
import numpy as np
from numpy.random import rand, choice
from copy import deepcopy
from typing import Optional, Tuple, List


class Representation:
    """
    Class defining types of representations
    """
    REAL: int = 0
    BINARY: int = 1
    PERMUTATION: int = 3


class Individual:
    """
    Class defining individual of population, represents one TrafficLight junction in simulation
    """
    def __init__(self, value: np.ndarray, repr_type: int = Representation.REAL):
        """
        :param value: the value representing individual (array)
        :param repr_type: representation type (default real valued vector)
        """
        self.value: np.ndarray = np.round(value, decimals=2)
        self.repr_type: int = repr_type
        self.repair()

    def repair(self) -> None:
        """
        Repairs green times to be in interval <MIN_GREEN, MAX_GREEN>

        :return: None
        """
        self.value = np.clip(self.value, MIN_GREEN_TIME, MAX_GREEN_TIME)


class Population:
    """
    Class representing all individual TrafficLights in simulation and current population
    """
    id: int = 0

    def __init__(self, pops: List[Individual], num_objectives: int = 2):
        """
        :param pops: individuals of population
        :param num_objectives: total objectives count, default 1
        """
        self.id = Population.id
        self.size: int = len(pops)
        self.pops: List[Individual] = pops
        self.fitness: Optional[Tuple[float, int]] = None  # (waiting time, arrived vehicles)
        self.objectives: int = num_objectives
        # NSGA-2 parameters
        self.rank: int = -1
        self.crowding_dist: int = -1
        Population.id += 1

    def crossover(self, other: 'Population', chance: float, op: callable) -> Tuple['Population', 'Population']:
        """
        :param other: other population to be used for crossover
        :param chance: chance for each individual traffic light to trigger crossover
        :param op: crossover operator
        :return: Two new populations produced by crossover operators
        """
        assert(other.size == self.size)
        child_a: List[Individual] = []
        child_b: List[Individual] = []
        for _ in range(self.size):
            i, j = choice(self.size, 2)
            a, b = None, None
            if rand() < chance:
                a, b = op(self.pops[i], other.pops[j])
            else:
                a, b = deepcopy(self.pops[i]), deepcopy(other.pops[j])
            child_a.append(a)
            child_b.append(b)
        return Population(child_a), Population(child_b)

    def mutate(self, chance: float, op: callable) -> None:
        """
        :param chance:  chance for each individual traffic light to trigger mutation
        :param op: mutation operator
        :return: None
        """
        for indiv in self.pops:
            if rand() < chance:
                op(indiv)
        return

    # ------------------------------ Utils ------------------------------

    def is_better(self, other: 'Population') -> bool:
        """
        Compares population based on objective values, depending on
        objectives (importance in ascending order -> i.e first by first objective, then by second ...).

        :param other: other population to be compared against
        :return: True if current is better than other, False otherwise
        """
        if self.fitness is None or other.fitness is None:
            raise ValueError("Error, expected fitness to be tuple, got type 'None' !")
        assert(len(self.fitness) >= self.objectives >= 1)
        assert(len(self.fitness) == len(other.fitness))
        # Compare objectives
        for i in range(self.objectives):
            if self.fitness[i] < other.fitness[i]:
                return True
            elif self.fitness[i] == other.fitness[i]:
                continue
            else:
                return False
        return True

    def dominates(self, other: 'Population') -> bool:
        """
        Domination of solutions in terms of minimization

        :param other: other population to be compared against
        :return: True if current dominates other, False otherwise
        """
        if self.fitness is None or other.fitness is None:
            raise ValueError("Error, expected fitness to be tuple, got type 'None' !")
        assert(len(self.fitness) >= self.objectives >= 1)
        assert(len(self.fitness) == len(other.fitness))
        return (
            all([self.fitness[i] <= other.fitness[i] for i in range(len(self.fitness))]) and
            any([self.fitness[i] < other.fitness[i] for i in range(len(self.fitness))])
        )

    def info(self, verbose: bool = False) -> None:
        """
        Prints information about population on the screen

        :param verbose: how informative should the output be
        :return: None
        """
        print(f"Population: {self.id} of size: {self.size}")
        print(f"Initialized: {self.pops is not None}")
        if self.pops is not None and verbose:
            print(f"Population vector: {[pop.value for pop in self.pops]}")
        print(f"Fitness -> (waiting time, arrived vehicles): {self.fitness[0], abs(self.fitness[1])}")

    # ------------------------------ Magics ------------------------------

    def __lt__(self, other: 'Population') -> bool:
        """
        Compares population based on objective values, depending on
        objectives (importance in ascending order -> i.e first by first objective, then by second ...).

        :param other: other population to be compared against
        :return: True if current is better (in terms of minimization) than other, False otherwise
        """
        return self.is_better(other)

