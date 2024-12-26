from utc.src.graph import Route
from typing import Optional, List, Dict, Tuple, FrozenSet, Set


class Cache:
    """
    Class uses for holding generated sub-graphs, provides utility methods.
    """
    def __init__(self, max_size: int = 1500):
        """
        :param max_size: maximal size of graphs which can be stored
        """
        self._memory: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], FrozenSet[int]] = {
            # (incoming_edges, outgoing_edges) -> edge id's ,....
        }
        self.invalid: Set[Tuple[Tuple[int, ...], Tuple[int, ...]]] = set()
        self.size: int = 0
        self.max_size: int = max_size

    def get_mapping(self, in_edges: Tuple[int, ...], out_edges: Tuple[int, ...]) -> Optional[FrozenSet[int]]:
        """
        :param in_edges: incoming edges
        :param out_edges: outgoing edges
        :return: set of internal edges id's forming subgraph, None if it does not exist
        """
        return self._memory.get((in_edges, out_edges), None)

    def has_mapping(self, in_edges: Tuple[int, ...], out_edges: Tuple[int, ...]) -> bool:
        """
        :param in_edges: incoming edges
        :param out_edges: outgoing edges
        :return: True if mapping exists, False otherwise
        """
        if (in_edges, out_edges) in self.invalid:
            return True
        return (in_edges, out_edges) in self._memory

    def save_mapping(
            self, in_edges: Tuple[int, ...], out_edges: Tuple[int, ...],
            routes: List[Route], replace: bool = False
        ) -> Optional[FrozenSet[int]]:
        """
        :param in_edges: incoming edges (id's, original)
        :param out_edges: outgoing edges (id's, original)
        :param routes: subgraph formed by list fo routes
        :param replace: if previous mapping should be replaced
        :return: Set of edges id's of routes forming sub-graph, None if mapping is invalid or error occurred
        """
        # Invalid mapping
        if routes is None or not routes:
            self.invalid.add((in_edges, out_edges))
            return None
        elif not replace and self.get_mapping(in_edges, out_edges) is not None:
            print(f"Cannot replace mapping: {in_edges} -> {out_edges}, as replace is set to false!")
            return None
        elif self.size + 1 > self.max_size:
            print(f"Cannot add mapping: {in_edges} -> {out_edges}, size: {self.size} is at maximum !")
            return None
        self.size += 1
        sub_graph: FrozenSet[int] = frozenset([edge_id for route in routes for edge_id in route.get_edge_ids(True)])
        self._memory[(in_edges, out_edges)] = sub_graph
        return sub_graph

    def clear(self) -> None:
        """
        Resets mapping, clears memory

        :return: None
        """
        self._memory.clear()
        self.invalid.clear()
        self.size = 0
