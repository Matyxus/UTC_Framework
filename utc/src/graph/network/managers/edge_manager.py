from utc.src.graph.network.managers.container import Container
from utc.src.graph.network.parts import Edge
from typing import Optional, Union, Iterable, Dict, List, Set, Tuple


class EdgeManager:
    """
    Class managing edges for graphs, provides utility methods
    """
    def __init__(self):
        super().__init__()
        # Mapping of out-going edge_id to other edge_ids that are incoming
        self.edge_connections: Dict[str, Set[str]] = {}
        self.edges: Dict[str, Edge] = {}
        self._edge_container: Container = Container(Edge, self.edges)

    # -------------------------------------------- Edges --------------------------------------------

    def add_edge(self, edge: Edge, replace: bool = False) -> bool:
        """
        :param edge: to be added
        :param replace: True if edge should be replaced (in case it already exists), False by default
        :return: True on success, false otherwise
        """
        return self._edge_container.add_object(edge, replace)

    def remove_edge(self, edge: Union[int, str, Edge]) -> bool:
        """
        :param edge: to be removed (either class or id)
        :return: True on success, false otherwise
        """
        return self._edge_container.remove_object(edge)

    def edge_exists(self, edge: Union[int, str, Edge], message: bool = True) -> bool:
        """
        :param edge: id (internal or original) of edge or class instance
        :param message: True if message about missing edge should be printed, True by default
        :return: True if edge exists, false otherwise
        """
        return self._edge_container.object_exists(edge, message)

    # -------------------------------------------- Getters --------------------------------------------

    def get_edges(
            self, edges: Iterable[Union[int, str, Edge]],
            message: bool = True, filter_none: bool = False
        ) -> List[Optional[Edge]]:
        """
        :param edges: of graph (string - original, or int for internal representation)
        :param message: True if message about missing object should be printed, True by default
        :param filter_none: True if None values should be filtered out of list, False by default
        :return: List of Edge instances (Some can be None if any edge object does not exist)
        """
        return self._edge_container.get_objects(edges, message, filter_none)

    def get_edge(self, edge: Union[int, str, Edge]) -> Optional[Edge]:
        """
        :param edge: of graph (string - original, or int for internal representation)
        :return: Edge object, None if Edge with given id does not exist
        """
        return self._edge_container.get_object(edge)

    def get_edges_junctions(self, edges: Iterable[Union[int, str, Edge]]) -> Optional[List[str]]:
        """
        :param edges: on path
        :return: List of junctions on edge sequence, None if any edge does not exist
        """
        edges: List[Optional[Edge]] = self.get_edges(edges)
        if None in edges:
            return None
        elif not edges:
            return []
        return [edges[0].from_junction] + [edge.to_junction for edge in edges]

    def get_edges_length(self) -> float:
        """
        :return: length of all edges in graph
        """
        return sum(edge.length for edge in self.edges.values())

    def get_edges_connections(self) -> Dict[str, Dict[str, Edge]]:
        """
        :return: Connection matrix made from edges mapping junction id to outgoing junctions and edge
        """
        ret_val: Dict[str, Dict[str, Edge]] = {}
        for edge in self.edges.values():
            if edge.from_junction in ret_val:
                ret_val[edge.from_junction][edge.to_junction] = edge
            else:
                ret_val[edge.from_junction] = {edge.to_junction: edge}
        return ret_val

    def get_edge_list(self) -> List[Edge]:
        """
        :return: List of Edge classes
        """
        return list(self.edges.values())

    # ------------------------------------------ Utils ------------------------------------------

    def get_longest_sequence(self, sequence: List[Union[int, str, Edge]]) -> Tuple[List[Edge], Tuple[int, int]]:
        """
        :param sequence: of edges
        :return: Longest common sequence of edges that is in the graph (can be empty),
        along with indexes of where the sequence was found
        """
        edges: List[Optional[Edge]] = self.get_edges(sequence, message=False)
        if not edges:
            return [], (-1, -1)
        elif None not in edges:
            return edges, (0, len(edges))
        edges.append(None)  # Add None in the back as stopping condition
        # Build sequence, filter 'None'
        best_left, best_right, left, right = 0, 0, 0, 0
        result: List[Edge] = []
        temp: List[Edge] = []
        while edges:
            current: Optional[Edge] = edges.pop(0)
            right += 1
            if current is None:
                if len(temp) > len(result):
                    best_left = left
                    best_right = right-1
                    result = temp
                temp = []
                left = right
                continue
            temp.append(current)
        return result, (best_left, best_right)

    def check_edge_sequence(self, sequence: List[Union[int, str, Edge]]) -> bool:
        """
        :param sequence: of edges
        :return: True if sequence is correct (we can use edges in this way), False otherwise
        """
        edges: List[Edge] = self.get_edges(sequence)
        if None in edges:
            return False
        # Check if edge sequence is correct
        current: Edge = edges.pop(-1)
        while edges:
            edge: Edge = edges.pop(-1)
            if current.get_id() not in self.edge_connections:
                # print(f"Invalid sequence: {sequence}, {current.get_id()} does not have any incoming edges!")
                continue
            elif edge.get_id() not in self.edge_connections[current.get_id()]:
                print(f"Invalid sequence: {sequence}, {edge.get_id()} is not incoming of: {current.get_id()} !")
                return False
            current = edge
        return True

    def load_edges(self, other: 'EdgeManager') -> bool:
        """
        :param other: EdgeManager class
        :return: True on success, false otherwise
        """
        # Checks
        if not isinstance(other, EdgeManager):
            print(f"Cannot load edges from other objects, expected: 'EdgeManager', got: '{type(other)}' !")
            return False
        return self._edge_container.load(other._edge_container)
