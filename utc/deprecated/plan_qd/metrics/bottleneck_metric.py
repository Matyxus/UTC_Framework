from utc.src.plan_qd.metrics.metric import Metric
from utc.src.graph import Route, Graph
from typing import List, Dict, Set, Tuple
import matplotlib.pyplot as plt


class BottleneckMetric(Metric):
    """
    Class finding bottleneck junctions in routes
    (bottleneck junction is junction which
    has many routes passing trough it
    from many different directions),
    and penalizing routes passing trough such junctions
    """
    def __init__(self):
        super().__init__("BottleneckMetric")
        self.bottlenecks: Dict[str, Dict[str, Tuple[List[int], float]]] = {
            # incoming_edge : { to_edge : ([route_index, ...], penalization), ...},
            # ...
            # }
        }
        # Matrix of types of edges, mapped to penalization (if going from lower/higher to lower/higher)
        self.edge_type_penalization: Dict[str, Dict[str, float]] = {
            "highway.primary": {
                "highway.primary": 1,
                "highway.secondary": 1.2,
                "highway.tertiary": 1.4,
                "highway.residential": 1.6
            },
            "highway.secondary": {
                "highway.primary": 1.2,
                "highway.secondary": 1,
                "highway.tertiary": 1.2,
                "highway.residential": 1.4
            },
            "highway.tertiary": {
                "highway.primary": 1.4,
                "highway.secondary": 1.2,
                "highway.tertiary": 1,
                "highway.residential": 1.2
            },
            "highway.residential": {
                "highway.primary": 1.6,
                "highway.secondary": 1.4,
                "highway.tertiary": 1.2,
                "highway.residential": 1
            }
        }
        # Penalization to subtract if passing trough traffic light system
        self.traffic_lights_penalization = 0.2
        self.routes_rank: Dict[int, float] = {}

    def calculate(self, routes: List[Route], graph: Graph, plot: bool = False, *args, **kwargs) -> None:
        self.clear()
        print(f"Using BottleneckMetric, finding bottlenecks ..")
        # Find bottlenecks junctions
        for index, route in enumerate(routes):
            edges: List[str] = route.get_edge_ids()
            junctions: List[str] = route.get_junctions()
            # Remove first and last junction (they cannot be bottlenecks),
            if len(junctions) > 2 and len(edges) > 2:
                junctions.pop(0)
                junctions.pop(-1)
            else:  # Route is too short, no point in ranking such route
                continue
            # Assume without last edge
            assert (len(edges)-1 == len(junctions))
            for i in range(len(edges)-1):
                from_edge: str = edges[i]
                to_edge: str = edges[i+1]
                # print(f"Checking connection of route: {route.get_id()} between: {from_edge} -> {to_edge}")
                assert (from_edge in graph.skeleton.edges)
                assert (to_edge in graph.skeleton.edges)
                # Missing junction because of simplification of graph
                if graph.skeleton.edges[from_edge].attributes["to"] not in graph.skeleton.junctions:
                    # print(f"Missing junction, simplified ...")
                    continue
                # Check penalization for such transition
                if from_edge not in self.bottlenecks:
                    self.bottlenecks[from_edge] = {}
                if to_edge not in self.bottlenecks[from_edge]:
                    # Add route index, calculate penalization
                    self.bottlenecks[from_edge][to_edge] = (
                        [index], self.penalization(from_edge, to_edge, graph)
                    )
                else:  # Add route index (already initialized and penalization is calculated)
                    self.bottlenecks[from_edge][to_edge][0].append(index)
        print(f"Finished finding bottlenecks, removing unavoidable ...")
        # Remove bottlenecks, which are unavoidable (all routes pass trough them)
        for incoming_edge_id in list(self.bottlenecks.keys()):
            # Edge has only one mapping and that mapping has all routes
            if len(self.bottlenecks[incoming_edge_id].keys()) == 1:
                for key in self.bottlenecks[incoming_edge_id].keys():
                    if len(self.bottlenecks[incoming_edge_id][key][0]) == len(routes):
                        del self.bottlenecks[incoming_edge_id]
                        # print(f"Deleted unavoidable edge mappping: {incoming_edge_id}")
        print(f"Finished removing unavoidable bottlenecks, ranking routes ...")
        # Rank routes
        self.routes_rank: Dict[int, float] = {
            i: 0 for i in range(len(routes))
        }
        for incoming_edge, value in self.bottlenecks.items():
            # Multiplier for multiple routes passing trough this junction from diff directions
            multiplier: int = len(value.keys())
            for to_edge, (route_indexes, penalization) in value.items():
                routes_count: int = len(route_indexes) * multiplier
                for route_index in route_indexes:
                    self.routes_rank[route_index] += round(penalization * routes_count, 1)
        # Sort by score given to each route index
        self.score = [i for i, _ in sorted(self.routes_rank.items(), key=lambda e: e[1])]
        print(f"Finished ranking routes")
        # Plot
        if plot:
            self.plot_ranking(routes, graph)

    def penalization(self, from_edge: str, to_edge: str, graph: Graph) -> float:
        """
        :param from_edge: incoming edge
        :param to_edge: out-coming edge
        :param graph: graph of road network
        :return: penalization for such passage
        """
        # Penalize different types of junctions
        # E.g. coming from non-main street to main
        # E.g. if the street has traffic lights (lessen the penalization)
        # ** E.g. when exiting junction to either Left / Right and needing to pass trough lanes
        # from opposite edge
        to_junction: str = graph.skeleton.edges[from_edge].attributes["to"]
        # print(f"Calculating penalization, coming from: '{from_edge}', trough: '{to_junction}', to: '{to_edge}'")
        from_edge_type: str = graph.skeleton.edges[from_edge].attributes.get("type", "highway.residential")
        from_edge_type = (from_edge_type if from_edge_type in self.edge_type_penalization else "highway.residential")
        to_ege_type: str = graph.skeleton.edges[to_edge].attributes.get("type", "highway.residential")
        to_ege_type = (to_ege_type if to_ege_type in self.edge_type_penalization else "highway.residential")
        ret_val: float = self.edge_type_penalization[from_edge_type][to_ege_type]
        # print(f"From edge is of type: '{from_edge_type}', to edge is of type: '{to_ege_type}'")
        if graph.skeleton.junctions[to_junction].is_traffic_light():
            # print(f"Junction has traffic lights, subtracting penalization: '{ret_val != 1}'")
            if ret_val != 1:
                ret_val -= self.traffic_lights_penalization
        # print(f"Final penalization: {ret_val}")
        return round(ret_val, 1)

    # -------------------------------------------- Utils --------------------------------------------

    def plot_ranking(self, routes: List[Route], graph: Graph, *args, **kwargs) -> None:
        fig, ax = graph.display.default_plot()
        for index in self.get_score(0.1):
            route = routes[index]
            ax.clear()
            graph.display.plot_default_graph(ax)
            route.plot(ax, color="blue")
            graph.display.add_label("_", "blue", f"Route: {index}, score: {round(self.routes_rank[index], 1)}")
            graph.display.make_legend(1)
            plt.tight_layout()
            fig.canvas.draw()
            plt.pause(0.1)
        graph.display.show_plot()

    def clear(self) -> None:
        super().clear()
        self.bottlenecks.clear()
