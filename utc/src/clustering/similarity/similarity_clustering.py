from utc.src.graph.network.parts import Route
from utc.src.clustering.similarity.dbscan_options import DbscanOptions
from joblib import Parallel, delayed
from typing import List, Dict, Tuple, Set, Optional, Union, Any
import numpy as np
from sklearn.cluster import DBSCAN


class SimilarityClustering:
    """
    Class clustering routes based on similarity,
    ordering routes based on diversity among clusters
    """
    def __init__(self, options: Optional[DbscanOptions] = None):
        """
        :param options: of similarity clustering
        """
        self.options: Optional[DbscanOptions] = options

    def run(self, routes: List[Route], sim_matrix: np.ndarray = None, reduced_dataset=None) -> Optional[List[int]]:
        """
        Shortened form far clustering, class must have been initiated with valid options

        :param routes: to be ranked by algorithm
        :param sim_matrix: pre-computed similarity matrix
        :param reduced_dataset: pre-compute result of DBSCAN
        :return: List of sorted route indexes, None if error occurred
        """
        if self.options is None:
            print("Cannot use method 'run' on 'SimilarityClustering', options are not set!")
        return self.calculate(
            routes, self.options.eps, self.options.min_samples,
            self.options.k, self.options.metric, self.options.min_routes,
            sim_matrix, reduced_dataset
        )

    def calculate(
            self, routes: List[Route],
            eps: float = 0.26, min_samples: int = 2, k: Union[int, float] = 1,
            metric: str = "shortest_length", min_routes: int = 10,
            sim_matrix: np.ndarray = None, reduced_dataset=None
            ) -> Optional[List[int]]:
        """
        :param routes: to be ranked by algorithm
        :param eps: minimal similarity between two routes for them to be added into same cluster
        :param min_samples: minimal amount of routes similar enough to be considered cluster
        :param k: number of best routes to be picked, if None only one best per cluster gets picked
        :param metric: type of sort (shortest_length by default)
        :param min_routes: minimal amount of routes to consider clustering
        :param sim_matrix: pre-computed similarity matrix
        :param reduced_dataset: pre-compute result of DBSCAN
        :return: List of sorted route indexes, None if error occurred
        """
        if len(routes) < min_routes:
            # print(f"DBSCAN received less then minimal amount {min_routes} of permissible routes!")
            return None
        # Can be pre-computed
        if sim_matrix is None:
            sim_matrix = self.create_matrix_parallel(routes)
            # Check matrix
            if sim_matrix is None:
                print("Cannot continue with DBSCAN, error at creating similarity matrix!")
                return None
        # Can be pre-computed
        if reduced_dataset is None:
            # print(f"Running DBSCAN")
            reduced_dataset = self.run_dbscan(sim_matrix, eps, min_samples)
            # Check data set
            if reduced_dataset is None:
                print("Output of dbscan is of type 'None', cannot continue !")
                return None
        return self.pick_best(sim_matrix, self.cluster_routes(reduced_dataset), metric, k)

    # -------------------------------------------- Sort --------------------------------------------

    def pick_best(self, sim_matrix: np.ndarray, clusters: Dict[int, List[int]], sort_by: str, k: int = 1) -> List[int]:
        """
        Picks K best routes, for float values, percentage is taken

        :param sim_matrix: similarity matrix of routes
        :param clusters: clusters made from routes by DBSCAN
        :param sort_by: one of: 'average_similarity', 'average_dissimilarity',
        'shortest_path', 'minimal_similarity', 'maximal_dissimilarity'
        :param k: number of best routes to be picked, if 1 only best per cluster gets picked
        :return: list of routed indexes
        """
        # print(f"Sorting cluster routes by '{sort_type}'")
        sorted_clusters: List[List[int]] = [
            # position of inner list acst as cluster id (-1 is on position 0, 0 on 1st, etc..)
            # values are route indexes (sorted)
        ]
        if sort_by in {"average_similarity", "average_dissimilarity"}:
            sorted_clusters = self.average_similarity_sort(sim_matrix, clusters, sort_by)
        elif sort_by in {"minimal_similarity", "maximal_similarity"}:
            sorted_clusters = self.maximal_similarity_sort(sim_matrix, clusters, sort_by)
        elif sort_by in {"shortest_length"}:
            # Routes are already sorted by their length (as this is the output of TopKA*)
            sorted_clusters = [cluster_routes for cluster_routes in clusters.values()]
        else:
            print(f"Unknown sort type: '{sort_by}'")
            return []
        # print(f"Sorting routes to final score")
        # Pick only one route (best) per cluster
        if k == 1:
            return [route_indexes[0] for route_indexes in sorted_clusters]
        elif k < 1:  # Pick fraction of routes
            k = max(int(sim_matrix.shape[0] * k), 1)
        else:  # Pick total of K routes
            k = int(k)
        # If we want to pick all routes, pick best each iteration in one cluster,
        # until all are empty (this makes it so, that all clusters routes are represented)
        ret_val: List[int] = []
        index: int = 0
        size: int = len(sorted_clusters)
        while sorted_clusters and index < k:
            if sorted_clusters[index]:  # Pop route index from cluster
                ret_val.append(sorted_clusters[index].pop(0))
            else:  # Empty cluster, pop it
                sorted_clusters.pop(index)
            index += 1
            if index >= size:
                index = 0
        # print(f"Finished sorting routes")
        return ret_val

    # noinspection PyMethodMayBeStatic
    def average_similarity_sort(
            self, sim_matrix: np.ndarray,
            clusters: Dict[int, List[int]], sort_by: str
            ) -> List[List[int]]:
        """
        Sorts routes based on intra-cluster average similarity,
        sorts clusters based on their routes averages

        :param sim_matrix: similarity matrix of routes
        :param clusters: clusters made from routes by DBSCAN
        :param sort_by: either 'average_similarity' or 'average_dissimilarity'
        :return: Sorted list of clusters containing indexes of their routes (also sorted)
        """
        similarity: bool = ("average_similarity" == sort_by)
        new_clusters: Dict[int, Tuple[float, List[Tuple[float, int]]]] = {
            # cluster_index: (average_similarity of all in-cluster routes,
            # [(average_similarity of this route, route index), ...]), ...
        }
        # Calculate avg. similarity of routes in clusters and avg. cluster similarity
        for cluster_id, routes_indexes in clusters.items():
            # For each route calculate its similarity compared to other routes in the same cluster
            cluster_size: int = min(len(routes_indexes), 2) - 1  # Minimum 2 because we subtract by 1
            average_similarities: List[Tuple[float, int]] = []
            for route_index in routes_indexes:
                average_similarities.append((
                    # Average similarity compared to other
                    # routes (subtract itself -> similarity of 1) / (number of routes -1 -> itself)
                    round((sim_matrix[route_index][routes_indexes].sum() - 1) / cluster_size, 3),
                    route_index
                ))
            cluster_size = len(routes_indexes)
            new_clusters[cluster_id] = (
                # Average of averages -> cluster average similarity
                round(sum([pair[0] for pair in average_similarities]) / cluster_size, 3),
                # Sort routes by their average similarity (sort in reverse if dissimilarity)
                sorted(average_similarities, key=lambda tup: tup[0], reverse=similarity)
            )
        # Sort clusters by average similarity (in reverse if dissimilarity)
        sorted_clusters_ids: list = sorted(
            new_clusters.items(), key=lambda tup: tup[1], reverse=similarity
        )
        # Return sorted routes
        return [[tup[1] for tup in lst] for lst in [cluster[1][1] for cluster in sorted_clusters_ids]]

    # noinspection PyMethodMayBeStatic
    def maximal_similarity_sort(
            self, sim_matrix: np.ndarray,
            clusters: Dict[int, List[int]], sort_by: str
        ) -> List[List[int]]:
        """
        Ranks routes in cluster based on average similarity to all other cluster routes

        :param sim_matrix: similarity matrix of routes
        :param clusters: clusters made from routes by DBSCAN
        :param sort_by: either 'minimal_similarity' or 'maximal_similarity'
        :return: Sorted list of clusters containing indexes of their routes (also sorted)
        """
        reverse: bool = (sort_by == "maximal_similarity")
        ranked_routes: List[List[Tuple[float, int]]] = [[] for _ in clusters.keys()]
        # ranked_routes[cluster] -> [(similarity compared to other cluster routes, route_index), ..]
        routes_count: int = sim_matrix.shape[0]
        for cluster, routes in clusters.items():
            for route in routes:
                all_sim: float = sim_matrix[route].sum()
                same_sim: float = sim_matrix[route][routes].sum()
                ranked_routes[cluster].append((round((all_sim - same_sim) / routes_count, 3), route))
            ranked_routes[cluster].sort(key=lambda tup: tup[0], reverse=reverse)
        # Return sorted routes
        return [[tup[1] for tup in cluster] for cluster in ranked_routes]

    # -------------------------------------------- Jaccard --------------------------------------------

    # noinspection PyMethodMayBeStatic
    def jaccard_similarity(self, r1: Set[int], r2: Set[int]) -> float:
        """
        Jaccard similarity = |r1 intersect r2| / |r1 union r2| ->\n
        (|r1 intersect r2| / (|r1| + |r2| - |r1 intersect r2|))

        :param r1: list of edge internal id's (of first route)
        :param r2: list of edge internal id's (of second route)
        :return: Jaccard similarity between two sets -> [0, 1]
        """
        intersect: int = len(r1 & r2)
        return intersect / (len(r1)+len(r2)-intersect)

    def create_matrix(self, routes: List[Route]) -> Optional[np.ndarray]:
        """
        :param routes: list of routes
        :return: matrix of routes similarities, None if number of routes is less than '2'
        """
        length: int = len(routes)
        # print(f"Computing Jaccard similarity matrix for: {length} routes")
        if length < 2:
            # print("Cannot create similarity matrix, length of routes list must be at least 2")
            return None
        matrix: np.array = np.zeros((length, length), dtype=np.float16)
        # Extract the edge id's (internal) sets, since we need all
        tmp: List[Set[int]] = [set(route.get_edge_ids(True)) for route in routes]
        for i in range(length-1):  # Skip main diagonal (as route has similarity of 1 to itself)
            r1: Set[int] = tmp[i]
            matrix[i, (i+1):] = [self.jaccard_similarity(r1, tmp[j]) for j in range(i+1, length)]
        # Compute the symmetric part
        matrix += matrix.T
        np.fill_diagonal(matrix, 1.0)
        # print("Finished computing Jaccard similarity matrix")
        return matrix

    def create_matrix_parallel(self, routes: List[Route], processes: int = 4) -> Optional[np.array]:
        """
        :param routes: list of routes (expected 1500 or more for parallel processing)
        :param processes: number of processes to be run on matrix creation (advantageous for larger amount of routes)
        :return: array containing similarity between each route (2D symmetric matrix), None if error occurred
        """
        # print(f"Computing Jaccard similarity matrix with {processes} processes")
        # -------------- Check args --------------
        length: int = len(routes)
        if length < 2:
            # print("Cannot create similarity matrix, length of routes list must be at least 2")
            return None
        elif processes > 1 and len(routes) < 1500:
            # print(f"Limiting processes: '{processes}' to 1, because amount of routes is: {len(routes)} < 1500")
            return self.create_matrix(routes)
        # -------------- Init --------------
        # Extract the edge id's (internal) sets, since we need all
        tmp: List[Set[int]] = [set(route.get_edge_ids(True)) for route in routes]

        def compute_row(row: int) -> List[float]:
            """
            Creates row for similarity matrix, used for parallel processing

            :param row: the current row we are computing
            :return: matrix row (upper triangle) of similarity values
            """
            s1: Set[int] = tmp[row]
            return [self.jaccard_similarity(s1, tmp[j]) for j in range(row+1, length)]

        # print(f"Starting to compute in parallel with: {processes} processes")
        results = Parallel(n_jobs=processes)(delayed(compute_row)(i) for i in range(length-1))
        matrix: np.array = np.zeros([length, length])
        for i, result in enumerate(results):
            matrix[i, (i+1):] = result
        matrix += matrix.T
        np.fill_diagonal(matrix, 1)
        # print("Finished computing Jaccard similarity matrix")
        return matrix

    # -------------------------------------------- Utils --------------------------------------------

    # noinspection PyMethodMayBeStatic
    def cluster_routes(self, labels) -> Optional[Dict[int, List[int]]]:
        """
        :param labels: computed by DBSCAN
        :return: mapping of cluster id to routes indexes, None if
        error occurred
        """
        if labels is None:
            print(f"Cannot cluster routes from labels of type 'None'")
            return None
        temp_clusters: Dict[int, List[int]] = {
            # cluster_index : [route_index (relative to inputted routes)]
        }
        # Create clusters, assign routes to them
        for index, label in enumerate(labels.labels_):
            if label not in temp_clusters:
                temp_clusters[label] = []
            temp_clusters[label].append(index)
        return temp_clusters

    # noinspection PyMethodMayBeStatic
    def run_dbscan(self, matrix: np.array, eps: float = 0.26, min_samples: int = 4) -> Optional[Any]:
        """
        :param matrix: similarity matrix of routes
        :param eps: minimal similarity between two routes for them to be added into same cluster
        :param min_samples: minimal amount of routes similar enough to be considered cluster
        :return: list of labels, None if arguments are invalid
        """
        if matrix is None:
            print("Invalid similarity matrix and/or routes received, cannot run DBSCAN!")
            return None
        elif matrix.shape[0] != matrix.shape[1]:
            print(f"Expected similarity matrix to be symmetric size, got: {matrix.shape} !")
            return None
        # Convert to Jaccard Distance instead of similarity
        return DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed').fit(np.ones(matrix.shape) - matrix)

