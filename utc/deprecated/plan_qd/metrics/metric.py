from utc.src.graph import Graph, Route
from typing import List, Union, Optional


class Metric:
    """
    General class providing framework for metric-type classes
    """

    def __init__(self, metric_name: str):
        """
        :param metric_name: name of metric
        """
        self.name = metric_name
        print(f"Initializing metric: '{self.name}' class")

    # noinspection PyMethodMayBeStatic
    def convert_k(self, k: Union[int, float, None], num_routes: int) -> Optional[int]:
        """
        :param k: number of best routes to pick (if float, used as percentage)
        :param num_routes: number of given routes to metric
        :return: k representation as int if it is not None, None otherwise
        :raises ValueError if k is incorrect
        """
        if k is None:
            return None
        elif isinstance(k, float) and not k.is_integer():
            if not (0 < k <= 1):
                raise ValueError(f"Expected float parameter 'k' to be between 0 and 1, got: '{k}' !")
            return max(int(num_routes * k), 1)
        else:  # k is int
            k: int = int(k)
            if k > num_routes:
                print(f"Received 'k': '{k}', which is greater than number of ordered routes: '{num_routes}'")
                return num_routes
            elif k < 1:
                raise ValueError(f"Expected integer parameter 'k' to higher than 0 got: '{k}' !")
            return k

    def calculate(
            self, routes: List[Route], graph: Graph,
            plot: bool = False, k: Union[int, float, None] = None,
            *args, **kwargs
            ) -> Optional[List[int]]:
        """
        :param routes: list of routes to rank
        :param graph: to which routes belong
        :param plot: bool, if metric ordering should be plotted, default false
        :param k: number of best routes to be picked, if None
        only one best per cluster gets picked
        :param args: additional args
        :param kwargs: additional args
        :return: list of sorted route indexes, None if error occurred
        """
        raise NotImplementedError("Method 'calculate' must be implemented by children of Metric!")

    # -------------------------------------------- Utils --------------------------------------------

    def plot_ranking(self, routes: List[Route], graph: Graph, *args, **kwargs) -> None:
        """
        Shows classification / ranking of routes done by algorithm

        :param routes: list of routes to rank
        :param graph: to which routes belong
        :param args: additional arguments
        :param kwargs: additional arguments
        :return: None
        """
        raise NotImplementedError("Error: method 'plot_ranking' must be implemented by children of Metric class!")
