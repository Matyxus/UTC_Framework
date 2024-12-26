from utc.src.graph.components import Graph, Route
from utc.src.constants.file_system import ProbabilityFile
from numpy import arange
from numpy.random import choice, seed
from random import sample
from typing import Dict, Tuple, List, Set, Optional, Any


class FlowFactory:
    """
    Class producing flows randomly, which entry and exit points are
    randomly selected from ProbabilityFile (weighted randomness), creates flows
    that have conflict (common junction) with at least one other.
    """
    def __init__(self, graph: Graph, prob_file: ProbabilityFile, allowed_flows: List[str] = None, seed_num: int = 42):
        """
        :param graph: graph of probability file
        :param prob_file: probability file for junction to junction flow existence
        :param allowed_flows: names of allowed flows
        :param seed_num: seed for random choice
        """
        seed(seed_num)
        self.graph: Graph = graph
        # Flows and their arguments, format strings
        self.allowed_flows: List[str] = (
            allowed_flows if allowed_flows is not None else ["random_flow", "exponential_flow", "uniform_flow"]
        )
        # Probability matrix of flows
        self.prob_matrix: Dict[str, Dict[str, int]] = prob_file.probability_matrix
        self.junctions: Set[str] = set()  # Junctions of currently selected flows
        self.routes: Dict[str, Dict[str, Route]] = {
            # from_junction : {to_junction : Route, ...}, ..
        }
        # Maximal amount of tries to choose destination junction
        self.max_tries: int = 50

    def generate_flows(self, start_time: int, end_time: int, amount: int = 0) -> List[Tuple[str, List[Any]]]:
        """
        :param start_time: starting time of flows
        :param end_time: ending time of flows
        :param amount: number of flows to be generated (default 0 -> randomly selected)
        :return: List of tuples (flow_type, flow_arguments) in
        format passed from command line
        """
        if not self.check_prob_matrix():
            return []
        elif amount <= 0:
            print(f"Parameter amount has to be at least '1', got: '{amount}'")
            return []

        def generate_flow(path: Tuple[str, str], time_interval: Tuple[int, int]) -> Tuple[str, List[Any]]:
            """
            :param path: tuple (from_junction, to_junction)
            :param time_interval: tuple (starting_time, ending_time)
            :return: tuple (flow_name, flow_args as list)
            """
            flow_name: str = choice(self.allowed_flows)
            args: List[Any] = []
            if flow_name == "random_flow":
                args = [*path, *sorted(choice(range(0, 15), size=2)), 20, *time_interval]
            elif flow_name == "uniform_flow":
                duration: int = end_time-start_time
                args = [
                    *path, choice(range(duration//5, duration//3)),
                    *time_interval, round(choice(arange(0.05, 0.2, 0.05)), 2)
                ]
            elif flow_name == "exponential_flow":
                args = [*path, *time_interval, round(choice(arange(0.75, 1.5, 0.1)), 2)]
            return flow_name, args

        ret_val: List[Tuple[str, List[Any]]] = []
        print(f"Generating {amount} flows")
        for route in self.generate_paths(amount):
            ret_val.append(generate_flow(
                (route.get_start(), route.get_destination()),
                (start_time, end_time)
            ))
        print(f"Finished generating flows")
        return ret_val

    def generate_paths(self, amount: int) -> List[Route]:
        """
        Generates routes which all have
        at least one 'conflict' with another,
        uses probability matrix from '.prob' file to
        perform weighted random choice between starting and
        ending junctions of routes

        :param amount: number of routes to be generated
        :return: list of routes
        """
        if amount < 1:
            print(f"Amount has to be at least '1', got: '{amount}'")
            return []
        # ------------- Init -------------
        routes: List[Route] = []
        starting_junctions: List[str] = list(self.prob_matrix.keys())
        print(f"Starting junctions: {starting_junctions}")
        probabilities: Dict[str, List[float]] = {
            # from_junction : [chance to pick, .... ]
        }
        for junction_id in starting_junctions:
            prob_sum: int = sum([i for i in self.prob_matrix[junction_id].values()])
            probabilities[junction_id] = [prob/prob_sum for prob in self.prob_matrix[junction_id].values()]
        # Junctions of currently found paths
        discovered: Set[str] = set()

        def generate_path() -> Optional[Route]:
            """
            Generates single route which has
            conflict with previously found routes

            :return: Route, or None if route could not have been found
            """
            route: Optional[Route] = None
            # Choose random starting junction (try only certain amount of times
            for starting_junction in sample(starting_junctions, len(starting_junctions)):
                # print(f"Starting search from: {starting_junction}")
                # Already explored
                if starting_junction in self.routes:
                    continue
                self.routes[starting_junction] = {}
                to_junctions: List[str] = list(self.prob_matrix[starting_junction].keys())
                # Choose random ending junction (try only certain amount of times)
                for to_junction in choice(to_junctions, p=probabilities[starting_junction], size=self.max_tries):
                    # print(f"Considering: {to_junction}")
                    # Already explored
                    if to_junction in self.routes[starting_junction]:
                        continue
                    route = self.graph.shortest_path.a_star(starting_junction, to_junction)[1]
                    self.routes[starting_junction][to_junction] = route
                    # No path or no "conflict" found between junctions of previous flows, search again
                    if route is None or not (set(route.get_junctions()) & discovered):
                        print(f"Route is 'None': {route is None}")
                        continue
                    return route
            return route
        # Find first route
        discovered = set(self.graph.skeleton.junctions.keys())
        # print(f"Generating random first route: ")
        routes.append(generate_path())
        if routes[0] is None:
            print(f"Unable to find route, increase 'max_tries' variable or check probability file !")
            return []
        discovered = set(routes[0].get_junctions())
        print(f"Generating routes with conflict (overlaps) for flows")
        for i in range(amount-1):
            # print(f"Generating {i}-th path")
            result: Route = generate_path()
            if result is None:
                print(f"Unable to find route, increase 'max_tries' variable or check probability file!")
                continue
            routes.append(result)
            # print(f"Found route: {result}")
            # print(f"Has conflict: {(set(result.get_junctions()) & discovered)}")
            discovered |= set(result.get_junctions())
            # print(f"Discovered: {discovered}")
        print(f"Finished generating routes")
        return routes

    # -------------------------------------- Utils --------------------------------------

    def check_prob_matrix(self) -> bool:
        """
        :return: true if probability matrix is correct, false otherwise
        """
        if self.graph is None:
            print(f"Graph is None, cannot check probability matrix!")
            return False
        elif not self.prob_matrix:
            print(f"Invalid probability matrix, either of type 'None' or empty!")
            return False
        for starting_junction in self.prob_matrix.keys():
            # Check starting junctions
            if starting_junction not in self.graph.skeleton.starting_junctions:
                print(f"Invalid starting junction: '{starting_junction}' for network: '{self.graph.skeleton.map_name}'")
                return False
            # Check destination junctions
            for destination_junction in self.prob_matrix[starting_junction].keys():
                if destination_junction not in self.graph.skeleton.ending_junctions:
                    print(
                        f"Invalid ending junction: '{destination_junction}' "
                        f"for network: '{self.graph.skeleton.map_name}'"
                    )
                    return False
        return True

