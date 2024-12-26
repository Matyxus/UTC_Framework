from utc.src.graph.modules.graph_module import GraphModule
from utc.src.graph.modules.display import Display
from utc.src.graph.network import RoadNetwork, Route, Junction
from typing import List, Set, Tuple, Dict


class Simplify(GraphModule):
    """ Class which contains methods for simplifying graph """

    def __init__(self, road_network: RoadNetwork = None):
        super().__init__(road_network)

    def simplify_graph(self, plot: Display = None) -> bool:
        """
        Simplifies graph by removing junctions forming roundabout, or those
        added by SUMO which are only for rendering/graphical reasons (they
        do not exist in '.osm' maps).

        :param plot: Class Display, if plot should be displayed (default None)
        :return: True on success, false otherwise
        """
        if not self.simplify_junctions(plot):
            return False
        return self.simplify_roundabouts(plot)

    def simplify_junctions(self, plot: Display = None) -> bool:
        """
        Finds junctions, that may be removed, e.g.
        A ----> B ---- > C (B can be removed),
        A <---> B <----> C (B can be removed),
        Takes out_route from B and merges it with in_route to B,
        for all out_routes, in_routes,
        should be called before simplify_roundabouts

        :param plot: Class Display, if plot should be displayed (default None)
        :return: True on success, false otherwise
        """
        # print("Simplifying junctions")
        # Junctions that cannot be removed
        non_removable: Set[str] = (self.road_network.starting_junctions | self.road_network.ending_junctions)
        for roundabout in self.road_network.roundabouts:
            non_removable |= set(roundabout)
        connections: Dict[str, List[Route]] = {}
        assert ((self.road_network.junctions.keys() & non_removable) == non_removable)
        # Find junctions that can be removed
        for junction_id in (self.road_network.junctions.keys() ^ non_removable):
            if self.junction_can_be_removed(junction_id):
                connections[junction_id] = []
        # Among junctions to be removed, find in_routes that are from junction
        # which is not removable, those without such routes are connected to another removable junction
        for junction_id in connections.keys():
            for in_route in self.road_network.junctions[junction_id].get_in_routes():
                if in_route.get_start() not in connections:
                    connections[junction_id].append(in_route)
        # ------------------ Simplification ------------------
        for junction_id, in_routes in connections.items():
            for in_route in in_routes:
                assert (in_route is not None and len(in_route.edge_list) == 1)
                current_route: Route = in_route
                # While we are traversing among removable junctions, connect routes
                destination: Junction = self.road_network.get_junction(current_route.get_destination())
                assert (destination.get_id() == junction_id)  # Sanity check
                while destination.get_id() in connections:
                    assert(len(destination.travel(current_route)) == 1)
                    # There can only be one route, that's why junction can be removed
                    out_route: Route = destination.travel(current_route)[0]
                    in_route |= out_route
                    current_route = out_route  # Move forward
                    destination = self.road_network.get_junction(current_route.get_destination())
                assert(in_route.get_destination() == destination.get_id())
                # Add new_route as new incoming route of last junction, remove outgoing of previous route
                # (We need to keep the outgoing route still, since it gets removed)
                destination.connections[in_route] = [] + destination.connections[current_route]
                destination.connections[current_route].clear()
                # Remove in_route from the original destination, since it has been modified
                start_junction: Junction = self.road_network.get_junction(in_route.edge_list[0].to_junction)
                start_junction.replace_in_route(in_route, None)
        # print("Finished merging routes")
        # ------------------ Plot ------------------
        if plot is not None:
            fig, ax = plot.initialize_plot()
            plot.render_graph(ax, colored=False)
            plot.render_junctions(ax, self.road_network.get_junctions(connections.keys()), colors="red")
            plot.add_label("o", "red", f"Removed Junctions: {len(connections)}")
            plot.make_legend(1)
            plot.show_plot(ax)
        # Remove junctions
        routes_count: int = len(self.road_network.routes)
        for junction_id in connections.keys():
            assert(self.road_network.remove_junction(junction_id, False, True))
        # print(
        #     f"Finished simplifying junctions, removed: {len(connections)} junctions "
        #     f"and {routes_count - len(self.road_network.routes)} routes"
        # )
        return True

    def simplify_roundabouts(self, plot: Display = None) -> bool:
        """
        Removes junctions forming roundabout, replaces them
        with new node (at center of mass position), adds new routes,
        removes previous routes between roundabout nodes,
        should be called after simplify_junctions

        :param plot: Class Display, if plot should be displayed (default None)
        :return: None
        """
        print(f"Simplifying roundabouts: {self.road_network.roundabouts}")
        for index, roundabout in enumerate(self.road_network.roundabouts):
            # ---------------- Variable setup ----------------
            roundabout_points: List[Tuple[float, float]] = []  # Position of each junction (x, y)
            roundabout_routes: Set[Route] = set()  # Routes on roundabout
            in_routes: Set[Route] = set()  # Routes connection to roundabout
            out_routes: Set[Route] = set()  # Routes coming out of roundabout
            for junction_id in roundabout:
                junction: Junction = self.road_network.junctions[junction_id]
                roundabout_points.append(junction.get_position())
                # Find all entry points to roundabout
                for in_route in junction.get_in_routes():
                    # Get edges going to roundabout
                    if not (in_route.get_start() in roundabout):
                        in_routes.add(in_route)
                # Find all exit points of roundabout
                for out_route in junction.get_out_routes():
                    # Get route going from roundabout
                    if not (out_route.get_destination() in roundabout):
                        out_routes.add(out_route)
                    else:  # Route leads to another roundabout junction
                        roundabout_routes.add(out_route)
            # ---------------- Setup new junction ----------------
            new_point: tuple = self.get_center_of_mass(roundabout_points)
            new_junction_id: str = f"r{index}"  # "r" for roundabout to not confuse with normal junctions
            new_junction: Junction = Junction(
                {"id": new_junction_id, "x": new_point[0], "y": new_point[1], "type": "roundabout"}
            )
            print(f"Creating new junction: {new_junction_id} representing roundabout: {roundabout}")
            # ---------------- From all entrances of roundabout form new routes ----------------
            for in_route in in_routes:
                starting_junction_id: str = in_route.get_destination()
                current_junction: Junction = self.road_network.junctions[starting_junction_id]
                assert (starting_junction_id in roundabout)  # Sanity check
                new_route: Route = Route([])  # New route for new junction
                # Since we entered roundabout, the only (possible) route now leads to another roundabout junction
                current_out_routes: Set[Route] = set(current_junction.travel(in_route))
                assert (len(current_out_routes) == 1)  # Sanity check
                route: Route = current_out_routes.pop()
                assert (route.get_destination() in roundabout)  # Sanity check
                new_route |= route  # Modify current route
                current_junction_id: str = route.get_destination()
                while current_junction_id != starting_junction_id:
                    current_junction = self.road_network.junctions[current_junction_id]
                    # print(f"Currently on junction: {current_junction_id}")
                    # Get all out coming routes
                    current_out_routes = set(current_junction.get_out_routes())
                    # Routes going out of current roundabout junction
                    routes_out_roundabout: Set[Route] = (current_out_routes & out_routes)
                    # Create new routes for each path leading out of roundabout
                    for out_route in routes_out_roundabout:
                        new_route_out: Route = (Route([]) | new_route | out_route)
                        self.road_network.add_route(new_route_out)  # Add new route to road_network of graph
                        new_junction.add_connection(in_route, new_route_out)  # Add new route to junction
                        # Add new incoming route to connected junction
                        destination: Junction = self.road_network.junctions[new_route_out.get_destination()]
                        destination.connections[new_route_out] = destination.connections[out_route]
                        # destination.replace_in_route(out_route, new_route_out)
                    assert (len(current_out_routes ^ routes_out_roundabout) == 1)
                    route = (current_out_routes ^ routes_out_roundabout).pop()
                    # print(f"Route: {self.routes[route_id]}")
                    current_junction_id = route.get_destination()
                    new_route |= route  # Move to next roundabout junction
                    # print(f"New route: {new_route}")
                current_junction = self.road_network.junctions[current_junction_id]
                assert (current_junction_id == starting_junction_id)
                # Now current_junction is equal to starting_junction
                # Check if starting junction has any out edges, add them as new route
                for out_route in (set(current_junction.get_out_routes()) & out_routes):
                    new_route_out: Route = (Route([]) | new_route | out_route)
                    # print(f"New route added to junction: {new_route_out}")
                    self.road_network.add_route(new_route_out)  # Add new route to road_network of graph
                    new_junction.add_connection(in_route, new_route_out)  # Add new route to junction
                    # Add new incoming route to connected junction
                    destination: Junction = self.road_network.junctions[new_route_out.get_destination()]
                    destination.connections[new_route_out] = destination.connections[out_route]
                    # destination.replace_in_route(out_route, new_route_out)
            self.road_network.roundabouts = []  # Empty list
            # ---------------- Remove ----------------
            # Remove routes on roundabout
            for route in roundabout_routes:
                self.road_network.remove_route(route)
            # Remove routes out of roundabout, connection on junctions
            for route in out_routes:
                destination: Junction = self.road_network.junctions[route.get_destination()]
                destination.remove_in_route(route)
                self.road_network.remove_route(route)
            # Set each out coming route of roundabout attribute["from"] as new junction
            for route in new_junction.get_out_routes():
                route.first_edge().attributes["from"] = new_junction_id
            # Set each incoming edge of roundabout, attribute["to"] as new junction
            for route in in_routes:
                route.last_edge().attributes["to"] = new_junction_id
            # Add new junction
            self.road_network.junctions[new_junction.attributes["id"]] = new_junction
            # ---------------- Plot ----------------
            if plot is not None:
                fig, ax = plot.initialize_plot()
                plot.render_graph(ax)
                plot.render_junctions(ax, self.road_network.get_junctions(roundabout), colors="red")
                plot.add_label("o", "red", "Roundabout junctions")
                plot.make_legend(1)
                plot.show_plot(ax)
            # Remove junctions forming roundabout
            for junction_id in roundabout:
                self.road_network.remove_junction(junction_id)
        print("Done simplifying roundabouts")
        return True

    # ----------------------------------- Utils -----------------------------------

    # noinspection PyMethodMayBeStatic
    def get_center_of_mass(self, points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        :param points: list of (x, y) coordinates
        :return: new (x, y) coordinate, which corresponds to center of mass
        """
        count: int = len(points)
        assert (count > 0)
        x: float = 0
        y: float = 0
        for i, j in points:
            x += i
            y += j
        return (x / count), (y / count)

    def junction_can_be_removed(self, junction_id: str) -> bool:
        """
        Only junctions with 2 in routes, 2 out routes or with 1 in route, 1 out route,
        can be removed from graph
        e.g. A ----> B ---> C, B can be removed
        e.g. A <----> B <---> C, B can be removed

        :param junction_id: to be checked
        :return: True if junction can be replaced, false otherwise
        """
        junction: Junction = self.road_network.get_junction(junction_id)
        if junction is None:
            return False
        in_routes: Set[Route] = set(junction.get_in_routes())
        out_routes: Set[Route] = set(junction.get_out_routes())
        length_in: int = len(in_routes)
        length_out: int = len(out_routes)
        if (length_in == 2 == length_out) or (length_in == 1 == length_out):
            overlapping_edges: Set[str] = set()
            # Check if traveling on different in_routes goes trough same edges
            for in_route in in_routes:
                for out_route in junction.travel(in_route):
                    edges: Set[str] = set(out_route.get_edge_ids())
                    # Edges overlap, cannot be replaced
                    if len(edges & overlapping_edges) != 0:
                        return False
                    overlapping_edges |= edges
            return True
        return False
