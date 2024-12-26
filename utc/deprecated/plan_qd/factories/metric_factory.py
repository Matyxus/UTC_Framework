from utc.src.plan_qd.metrics import SimilarityMetric
from utc.src.graph.components import Skeleton, Graph, Route
from utc.src.constants.file_system import ProbabilityFile
from typing import Dict, Tuple, List, Set, Optional, Any


class MetricFactory:
    """
    Class enabling use of metric commands in efficient setting (provides method to pre-compute
    needed objets e.g. similarity matrix for SimilarityMetric) for multiple metric calls
    """
    def __init__(self):
        self.similarity_metric: Optional[SimilarityMetric] = None

    def initialize_metric(self, name: str) -> None:
        """
        :param name: of metric class to be initialized
        :return: None
        """
        if name == "similarity_metric":
            self.similarity_metric = SimilarityMetric()
        else:
            print(f"Unknown name of metric: {name}")




# For testing purposes
if __name__ == "__main__":
    pass


