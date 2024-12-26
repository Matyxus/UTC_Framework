from utc.src.graph.modules.graph_module import GraphModule
from utc.src.graph.network import RoadNetwork, Route
from utc.src.graph.modules.display import Display, plt
import heapq
from typing import Dict, List, Tuple, Optional


class PathFinder(GraphModule):
    """ Class implementing shortest path algorithms """
    def __init__(self, road_network: RoadNetwork):
        super().__init__(road_network)

    # -------------------------------------- Shortest path --------------------------------------

    def top_k_a_star(
            self, start_junction_id: str, target_junction_id: str,
            c: float, k: int = 3000, display: Display = None,
            incoming_route: Route = None
        ) -> Optional[List[Route]]:
        """
        At start, performs A* search to find shortest route,
        uses unexplored junction remaining in queue from the initial call of A* to find K other routes.
        K in this case can be limited by parameter c, which sets the maximal length
        of new routes to be at maximum c * shortest_route_length

        :param start_junction_id: starting junction
        :param target_junction_id: target junction
        :param c: multiplier of shortest path length
        :param k: limit of found routes, default 3000
        :param display: Class Display, if process should be displayed (default None)
        :param incoming_route: incoming route to starting junction (default None)
        :return: List of routes (shortest route is the first) satisfying (route_length < c * shortest_route_length),
        None if shortest route does not exists
        """
        # -------------------------------- checks --------------------------------
        if not self.check_junctions(start_junction_id, target_junction_id):
            return None
        elif c <= 1:
            print(f"Parameter 'c' has to be greater than 1, got: '{c}' !")
            return None
        elif k <= 1:
            print(f"Parameter 'k' has to be more than 1, got: '{k}' !")
            return None
        # -------------------------------- init --------------------------------
        # Perform initial search to find shortest route and return queue with unexplored junctions
        queue, shortest_route = self.a_star(start_junction_id, target_junction_id, incoming_route)
        if shortest_route is None:  # No path exists
            print(f"No path exists between junction '{start_junction_id}' and junction '{target_junction_id}'")
            return None
        dest: Tuple[float, float] = self.road_network.junctions[target_junction_id].get_position()
        limit: float = round(c * shortest_route.traverse()[0], 3)
        assert (limit > 0)
        # print(f"Setting alternative route length limit: '{limit}'")
        other_routes: List[Route] = [shortest_route]
        # -------------------------------- Algorithm --------------------------------
        while queue:
            priority, in_route, length, path = heapq.heappop(queue)
            if priority > limit:  # Priority is current length + euclidean distance to target
                break  # End of search
            elif in_route.get_destination() == target_junction_id and in_route.allowed_last:
                # Found other path (satisfying path_length < c * shortest_path_length), record it
                assert (length <= limit)
                assert (self.road_network.check_edge_sequence(path))
                assert (len(set(path)) == len(path))
                other_routes.append(Route(self.road_network.get_edges(path)))
                assert (other_routes[-1].traverse()[0] <= limit)
                if len(other_routes) > k:
                    print(f"Reach limit of k={k} routes found, stopping search ...")
                    break
                continue
            for route in self.road_network.junctions[in_route.get_destination()].travel(in_route):
                distance, neigh_junction_id = route.traverse()
                # On the same route, avoid visiting the same edge multiple times (loops)
                if not self.has_loop(route, path):
                    distance += length
                    # Current position
                    pos: Tuple[float, float] = self.road_network.junctions[neigh_junction_id].get_position()
                    heapq.heappush(queue, (
                        distance + self.coord_distance(dest, pos), route,
                        distance, path + route.get_edge_ids(True)
                        )
                    )
                    # self.tie_breaker += 1
        # print(f"Finished finding routes, found another: '{len(other_routes) - 1}' routes")
        queue = None  # Free memory
        # -------------------------------- Plot --------------------------------
        if display is not None:  # Show animation of routes
            fig, ax = display.initialize_plot()
            for index, route in enumerate(other_routes):
                ax.clear()
                display.render_graph(ax, colored=False)
                display.render_junctions(ax, [self.road_network.get_junction(start_junction_id)], colors="green")
                display.render_junctions(ax, [self.road_network.get_junction(target_junction_id)], colors="red")
                display.render_routes(ax, [route], colors="blue")
                display.add_label("_", "blue", f"Route: '{index}', length: '{round(route.traverse()[0])}'")
                display.make_legend(1)
                plt.tight_layout()
                fig.canvas.draw()
                plt.pause(0.1)
            display.show_plot(ax)
        return other_routes

    def a_star(
            self, start_junction_id: str,
            end_junction_id: str, in_route: Route = None
        ) -> Tuple[List[tuple], Optional[Route]]:
        """
        Standard implementation of A* algorithm, with added support for multi-graphs (which
        can prevent A* from finding shortest path)

        :param start_junction_id: starting junction
        :param end_junction_id: goal junction
        :param in_route: incoming route to starting junction (Default None)
        :return: Queue containing unexplored junctions, shortest route (None if it could not be found)
        """
        # print(f"Finding shortest route from: {start_junction_id}, to: {end_junction_id} using A* algorithm")
        # -------------------------- Init --------------------------
        # priority, in_route, path (list containing all visited edges)
        queue: List[Tuple[float, Route, float, List[int]]] = []
        shortest_route: Optional[Route] = None
        if not self.check_junctions(start_junction_id, end_junction_id):
            return queue, shortest_route
        destination_pos: Tuple[float, float] = self.road_network.get_junction(end_junction_id).get_position()
        # For junction n, gScore[n] is the cost of the cheapest path from start to n currently known,
        # reworked to be mapping to routes (since road-network, can be multi-graph)
        g_score: Dict[Route, float] = {route: float("inf") for route in self.road_network.routes.values()}
        # Use all incoming routes as starting points (if they have any out-going routes)
        if in_route is None:
            for out_route in self.road_network.junctions[start_junction_id].get_out_routes():
                if not out_route.allowed_first:
                    continue
                distance, neigh_junction_id = out_route.traverse()
                # Current position
                pos: Tuple[float, float] = self.road_network.junctions[neigh_junction_id].get_position()
                g_score[out_route] = distance  # Update distances
                heapq.heappush(queue, (
                    distance + self.coord_distance(destination_pos, pos), out_route,
                    distance, out_route.get_edge_ids(True)
                    )
                )
        else:
            print(f"TopkA* running with incoming route: {in_route}")
            assert (in_route in self.road_network.junctions[start_junction_id].connections)
            assert (len(self.road_network.junctions[start_junction_id].travel(in_route)) != 0)
            g_score[in_route] = 0
            heapq.heappush(queue, (0, in_route, 0, []))
        # Empty queue
        if not queue:
            print(f"Unable to find any incoming route to junction: {start_junction_id}")
            return queue, shortest_route
        # -------------------------- Algorithm --------------------------
        while queue:
            priority, in_route, length, path = heapq.heappop(queue)  # Removes and returns
            # print(f"Traveling: {length}, {in_route}, {current_junction}, {path}")
            # Found shortest path
            if in_route.get_destination() == end_junction_id and in_route.allowed_last:
                assert (self.road_network.check_edge_sequence(path))
                assert (len(set(path)) == len(path))
                shortest_route = Route(self.road_network.get_edges(path))
                break
            for route in self.road_network.junctions[in_route.get_destination()].travel(in_route):
                distance, neigh_junction_id = route.traverse()
                distance += g_score[in_route]
                if distance < g_score[route] and not self.has_loop(route, path):
                    pos: Tuple[float, float] = self.road_network.junctions[neigh_junction_id].get_position()
                    g_score[route] = distance
                    heapq.heappush(queue, (
                        distance + self.coord_distance(destination_pos, pos), route,
                        distance, path + route.get_edge_ids(True)
                        )
                    )
        # print(f"Finished finding shortest route: {shortest_route}")
        return queue, shortest_route

    # -------------------------------------- Utils --------------------------------------

    # noinspection PyMethodMayBeStatic
    def has_loop(self, route: Route, path: List[int]) -> bool:
        """
        :param route: currently considered route
        :param path: all visited edges on path
        :return: True if there is overlap between route edges and visited edges, False otherwise
        """
        return route.edge_list[0].internal_id in path

    # noinspection PyMethodMayBeStatic
    def coord_distance(self, point_a: Tuple[float, float], point_b: Tuple[float, float]) -> float:
        """
        :param point_a: first point
        :param point_b: second point
        :return: absolute distance between points (3 decimal precision)
        """
        return round((((point_a[0] - point_b[0]) ** 2) + ((point_a[1] - point_b[1]) ** 2)) ** 0.5, 3)

    def check_junctions(self, start_junction_id: str, end_junction_id: str) -> bool:
        """
        :param start_junction_id: where should search start
        :param end_junction_id: where should search end
        :return: True if both junctions exist and are not equal, False otherwise
        """
        if not (self.road_network.junction_exists(start_junction_id) and
                self.road_network.junction_exists(end_junction_id)):
            return False
        return True
