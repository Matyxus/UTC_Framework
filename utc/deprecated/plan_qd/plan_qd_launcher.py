from utc.deprecated.graph_main import GraphMain, Command, FilePaths
from utc.src.graph.components import Skeleton, Route
from utc.src.plan_qd.metrics import SimilarityMetric
from utc.src.constants.file_system import MyFile, MyDirectory, DirPaths
from typing import List, Dict, Tuple, Optional, Union


class PlanQDLauncher(GraphMain):
    """
    Class launching methods for plan quality & diversity testing, extends GraphMain
    """
    def __init__(self, log_commands: bool = True):
        super().__init__(log_commands)
        self.similarity_metric: SimilarityMetric = SimilarityMetric()
        # Routes used to create graphs
        self.subgraph_routes: Dict[str, List[Route]] = {}
        # Current values of similarity matrix and DBSCAN output
        self.similarity_matrix = None
        self.reduced_dataset = None

    def initialize_commands(self) -> None:
        super().initialize_commands()
        # Add commands for metrics
        self.user_input.add_command([
            Command("similarity_metric", self.similarity_metric_command)
        ])

    # --------------------------------- Commands ---------------------------------

    def subgraph_command(
            self, subgraph_name: str, graph_name: str, from_junction: str,
            to_junction: str, c: float, plot: bool = False
         ) -> Optional[List[Route]]:
        ret_val = super().subgraph_command(subgraph_name, graph_name, from_junction, to_junction, c, plot)
        if ret_val is not None:
            self.subgraph_routes[subgraph_name] = ret_val
        return ret_val

    def similarity_factory(
            self, sort_by_list: List[str], scenario_name: str,
            file_name: str, param_k: Union[int, float, None],
            processes: int = 1
            ) -> Optional[List[Tuple[bool, str]]]:
        """
        Creates sub-graphs based on given sort types for similarity_metric,
        it is assumed that scenario already has initialized metric directory and
        that it exists

        :param sort_by_list: options by which similarity metric will sort routes by
        :param scenario_name: name of scenario folder
        where sub-graphs will be saved (in /maps/networks directory)
        :param file_name: under which sub-graphs will be saved
        (adds custom suffix based on metric)
        :param param_k: number of best routes to be picked, if None
        only one best per cluster gets picked
        :param processes: number of processes that can be run in parallel to create
        similarity matrix, 1 by default
        :return: list of tuples (true/false if subgraph was generated successfully,
        subgraph file_name), None if error occurred
        """
        # Checks
        if not MyDirectory.dir_exist(DirPaths.SCENARIO.format(scenario_name)):
            return None
        elif not MyDirectory.dir_exist(DirPaths.SCENARIO_MAPS.format(scenario_name)):
            return None
        print(f"Creating subgraphs for similarity_metric ({sort_by_list}), k: {param_k}")
        ret_val: Optional[List[Tuple[bool, str]]] = []
        # First create subgraph for all sort types, we do this first to release memory of
        # similarity matrix (can be huge -> 10000x10000 ~ 800MB)
        # For each previously created subgraph (trough Top_K_A* -> subgraph_command method)
        for i, subgraph in enumerate(list(self.subgraph_routes.keys())):
            # Initialize similarity matrix and DBSCAN (compute before sorting routes)
            print(f"Pre-computing similarity matrix & DBSCAN")
            self.similarity_matrix = self.similarity_metric.create_jaccard_matrix_parallel(
                self.subgraph_routes[subgraph], processes=processes
            )
            self.reduced_dataset = self.similarity_metric.run_dbscan(self.similarity_matrix)
            print(f"Creating sub-graphs {i+1}/{len(self.subgraph_routes)}, from: {subgraph}")
            # Create sub-graphs
            for sort_by in sort_by_list:
                success: bool = self.similarity_metric_command(
                    f"{sort_by}_{i}", subgraph, param_k,
                    sort_by=sort_by
                )
                # Error at subgraph creation
                if not success:
                    return
                print(f"Finished subgraph: {i + 1}/{len(sort_by_list)}")
            # Empty route list to free memory
            self.subgraph_routes[subgraph] = []
        # Free memory
        self.similarity_matrix = None
        self.reduced_dataset = None
        # Save sub-graphs
        for sort_by in sort_by_list:
            curr_file_name = file_name.replace("_default", "_similarity_" + sort_by)
            # First subgraph
            sub_graph_name: str = f"{sort_by}_0"
            # Merge
            for i in range(1, len(self.subgraph_routes)):
                self.merge_command(sub_graph_name, sub_graph_name, f"{sort_by}_{i}")
            # Save
            self.save_graph_command(sub_graph_name, curr_file_name, scenario_name=scenario_name)
            # Remove
            for i in range(len(self.subgraph_routes)):
                self.graphs.pop(f"{sort_by}_{i}", None)
            print(f"Finished creating subgraph for similarity_metric_{sort_by}: {curr_file_name}")
            ret_val.append(
                (MyFile.file_exists(FilePaths.SCENARIO_MAP.format(scenario_name, curr_file_name)), curr_file_name)
            )
        return ret_val

    @GraphMain.log_command
    def similarity_metric_command(
            self, new_subgraph: str, subgraph: str, k: Union[int, float, None], eps: float = 0.26,
            min_samples: int = 4, sort_by: str = "average_similarity", plot: bool = False
            ) -> bool:
        """
        Cluster routes based on similarity, uses
        'order_by' parameter to sort them (from best to worst),
        sorted list is then used to construct new subgraph

        :param new_subgraph: name of newly created subgraph by metric
        :param subgraph: name created by 'sub_graph' command
        :param k: number of best routes to pick (if float, used as percentage)
        :param eps: minimal similarity between two routes for them to be added into same cluster
        :param min_samples: minimal amount of routes similar enough to be considered cluster
        :param sort_by: method to use to sort clusters by
        :param plot:
        :return: true on success, false otherwise
        """
        if not self.graph_exists(subgraph):
            return False
        elif subgraph not in self.subgraph_routes:
            print(f"Missing subgraph: {subgraph} logged in subgraph routes!")
            return False
        ranking: List[int] = self.similarity_metric.calculate(
            self.subgraph_routes[subgraph], eps=eps,
            min_samples=min_samples,
            sort_by=sort_by, sim_matrix=self.similarity_matrix,
            reduced_dataset=self.reduced_dataset, k=k
        )
        if not ranking:
            print(f"Invalid ranking, could not create subgraph ...")
            return False
        sub_graph: Skeleton = self.graph.sub_graph.create_sub_graph(
            [self.subgraph_routes[subgraph][index] for index in ranking]
        )
        if sub_graph is None:
            print("Could not create subgraph")
            return False
        sub_graph.set_name(new_subgraph)
        self.graphs[new_subgraph] = sub_graph
        print(f"Finished creating sub-graph: {new_subgraph}")
        return True


if __name__ == "__main__":
    temp: PlanQDLauncher = PlanQDLauncher()
    temp.run()
