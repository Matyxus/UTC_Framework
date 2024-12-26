from utc.src.semestral.evolutionary.indiv import Individual, Population
from utc.src.semestral.tl_constants import MIN_GREEN_TIME, MAX_GREEN_TIME
import numpy as np
from typing import List, Dict, Tuple


class Initialization:
    """
    Class containing initialization operators ad static methods.
    """

    @staticmethod
    def random_init(count: int, size: int) -> List[Individual]:
        """
        :param count: total count of numbers to be present in Individual
        :param size: size of population to be initialized
        :return: Randomly initialized population of individuals (using uniform distribution)
        """
        return [Individual(np.random.uniform(MIN_GREEN_TIME, MAX_GREEN_TIME, count)) for _ in range(size)]


class Selection:
    """
    Class containing selection operators ad static methods.
    """

    @staticmethod
    def tournament(pops: List[Population], size: int, k: int = 3) -> List[int]:
        """
        Standard tournament selection for GeneticAlgorithms, assumes population is already sorted

        :param pops: list of population
        :param size: how many should be selected
        :param k: how many pops are chosen for each tournament
        :return: List of indexes of selected populations for next generation
        """
        return [min(np.random.choice(len(pops), k)) for _ in range(size)]

    @staticmethod
    def rank_binary_tournament(pops: List[Population], size: int) -> List[int]:
        """
        Rank based selection for NSGA-2 algorithm

        :param pops: list of population
        :param size: how many should be selected
        :return: List of indexes of selected populations for next generation
        """
        indexes: List[int] = []
        for i, j in zip(np.random.choice(len(pops), size), np.random.choice(len(pops), size)):
            if pops[i].rank < pops[j].rank:
                indexes.append(i)
            elif pops[i].rank == pops[j].rank and pops[i].crowding_dist > pops[j].crowding_dist:
                indexes.append(i)
            else:
                indexes.append(j)
        return indexes


class Crossover:
    """
    Class containing crossover operators ad static methods.
    """

    @staticmethod
    def blend_crossover(a: Individual, b: Individual, alpha: float = 0.5) -> Tuple[Individual, Individual]:
        """
        :param a: first individual
        :param b: second individual
        :param alpha: multiplying factor (optimal is around 0.5)
        :return: Two new individuals
        """
        child_a: np.ndarray = np.zeros(a.value.size)
        child_b: np.ndarray = np.zeros(a.value.size)
        for i in range(a.value.size):
            hi, lo = (a.value[i], b.value[i]) if (a.value[i] > b.value[i]) else (b.value[i], a.value[i])
            # We need to avoid multiplying by 0, if parents are equal
            d: float = abs(hi-lo) * alpha + 0.001
            child_a[i], child_b[i] = np.random.uniform(lo-d, hi+d, 2)
        return Individual(child_a), Individual(child_b)


class Mutation:
    """
    Class containing mutation operators ad static methods.
    """

    @staticmethod
    def gaussian(indiv: Individual) -> None:
        """
        Changes individual's value by normal (gaussian) mutation with sigma 0 and expect value 1.

        :param indiv: to be mutated
        :return: None
        """
        indiv.value += np.random.normal(0, 1, indiv.value.size)
        indiv.repair()
        return

    @staticmethod
    def uniform(indiv: Individual) -> None:
        """
        Replaces the value of individual by randomly choosing from uniform distribution
        (Limited by min and max green timer).

        :param indiv: to be mutated
        :return: None
        """
        indiv.value = np.random.uniform(MIN_GREEN_TIME, MAX_GREEN_TIME, indiv.value.size)
        indiv.repair()
        indiv.value = np.round(indiv.value, decimals=2)
        return


# All operators
OPERATORS: Dict[str, Dict[str, callable]] = {
    "initialization": {"random": Initialization.random_init},
    "selection": {
        "tournament": Selection.tournament,
        "rank_binary_tournament": Selection.rank_binary_tournament
    },
    "crossover": {"blend": Crossover.blend_crossover},
    "mutation": {
        "gaussian": Mutation.gaussian,
        "uniform": Mutation.uniform
    }
}


def operator_exists(op_type: str, op_name: str) -> bool:
    """
    :param op_type: type of operators (initialization, selection, crossover or mutation)
    :param op_name: name of operators
    :return: True if given operator type and name exists, False otherwise
    """
    if op_type not in OPERATORS:
        print(f"Unknown operator type: {op_type}, available: {OPERATORS.keys()}")
        return False
    elif op_name not in OPERATORS[op_type]:
        print(f"Unknown operator {op_type}: {op_name}, available: {OPERATORS[op_type].keys()}")
        return False
    return True
