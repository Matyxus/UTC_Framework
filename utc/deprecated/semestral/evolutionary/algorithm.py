from utc.src.semestral.evolutionary.indiv import Population
from utc.src.semestral.evolutionary.operators import operator_exists
from typing import Optional, Union, List, Set


class Algorithm:
    """
    Super class for all Evolutionary algorithms, implements helper methods and variables.
    """
    def __init__(self, name: str, params: dict):
        """
        :param name: name of the algorithm
        :param params: parameters of algorithm
        """
        self.name: str = name
        self.params: dict = params
        assert(self.default_check() and self.check_params())
        self.population: Optional[Union[List[Population], Population]] = None

    def step(self, iteration: int) -> Optional[Union[List[Population], Population]]:
        """
        :param iteration:
        :return:
        """
        raise NotImplementedError("Error, method: 'step' must be implemented by children of Algorithm!")

    def init_population(self, phases: int, size: int) -> None:
        """
        :param phases: number of phases each TL has
        :param size: number of TLs in simulation
        :return: None
        """
        raise NotImplementedError("Error, method: 'step' must be implemented by children of Algorithm!")

    # ------------------------------------- Utils -------------------------------------

    def check_params(self) -> bool:
        """
        :return: True if parameters given to algorithm are correct, false otherwise
        """
        raise NotImplementedError("Error, method: 'check_params' must be implemented by children of Algorithm!")

    def evaluate_population(self, population: Union[List[Population], Population]) -> bool:
        """
        :param population: population to be evaluated
        :return: True on success, False otherwise
        """
        return self.params["fitness"](population)

    def default_check(self) -> bool:
        """
        :return: True if default parameters of Algorithm Class are present, False otherwise
        """
        keys: Set[str] = {
            "selection", "initialization",
            "population", "fitness",
            "crossover", "crossover_chance",
            "mutation", "mutation_chance"
        }
        if len(keys & self.params.keys()) != len(keys):
            print(f"Error, missing parameters: {keys ^ (keys & self.params.keys())}")
            return False
        # Check operator existence
        for op in ["initialization", "selection", "crossover", "mutation"]:
            if not operator_exists(op, self.params[op]):
                return False
        # Check operator values
        for op in ["crossover_chance", "mutation_chance"]:
            if not isinstance(self.params[op], (int, float)) and 0 <= self.params[op] <= 1:
                print(f"Expected operator: {op} to be number in range (0, 1), got: {self.params[op]}")
                return False
        # Check that population is non-zero
        if not isinstance(self.params["population"], int) and self.params[op] >= 1:
            print(f"Expected parameter: population to be number >= 1, got: {self.params['population']}")
            return False
        # Check fitness
        if not callable(self.params["fitness"]):
            print("Error, fitness must be function!")
            return False
        return True

    def is_running(self) -> bool:
        """
        :return: True if algorithm is running, false otherwise
        """
        raise NotImplementedError("Error, method: 'is_running' must be implemented by children of Algorithm!")



