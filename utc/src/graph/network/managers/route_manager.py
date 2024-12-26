from utc.src.graph.network.managers.container import Container
from utc.src.graph.network.parts import Route
from typing import List, Dict, Optional, Union, Iterable


class RouteManager:
    """
    Class managing routes for graphs, provides utility methods
    """
    def __init__(self):
        super().__init__()
        self.routes: Dict[str, Route] = {}
        self._route_container: Container = Container(Route, self.routes)

    # -------------------------------------------- Routes --------------------------------------------

    def add_route(self, route: Route, replace: bool = False) -> bool:
        """
        :param route: to be added to dictionary of routes
        :param replace: True if route should be replaced (in case it already exists), False by default
        :return: True on success, false otherwise
        """
        if route.is_temporary():
            return False
        return self._route_container.add_object(route, replace)

    def remove_route(self, route: Union[int, str, Route]) -> bool:
        """
        :param route: to be removed
        :return: True on success, false otherwise
        """
        # Lower the number of references on edges
        for edge in route.edge_list:
            edge.references -= 1
        return self._route_container.remove_object(route)

    def route_exists(self, route: Union[int, str, Route], message: bool = True) -> bool:
        """
        :param route: id of route or class instance
        :param message: True if message about missing route should be printed, True by default
        :return: True if route exists, false otherwise
        """
        return self._route_container.object_exists(route, message)

    # -------------------------------------------- Getters --------------------------------------------

    def get_routes(
            self, routes: Iterable[Union[str, int, Route]],
            message: bool = True, filter_none: bool = False
        ) -> List[Optional[Route]]:
        """
        :param routes: of graph (string - original, or int for internal representation)
        :param message: True if message about missing object should be printed, True by default
        :param filter_none: True if None values should be filtered out of list, False by default
        :return: List of Route instances (Some can be None if any given route does not exist)
        """
        return self._route_container.get_objects(routes, message, filter_none)

    def get_route(self, route: Union[int, str, Route]) -> Optional[Route]:
        """
        :param route: of graph
        :return: Route object, None if Route with given id does not exist
        """
        return self._route_container.get_object(route)

    def get_routes_list(self) -> List[Route]:
        """
        :return: List of Route classes
        """
        return list(self.routes.values())

    # -------------------------------------------- Utils --------------------------------------------

    def load_routes(self, other: 'RouteManager') -> bool:
        """
        :param other: RouteManager class
        :return: True on success, false otherwise
        """
        # Checks
        if not isinstance(other, RouteManager):
            print(f"Cannot load routes from other objects, expected: 'RouteManager', got: '{type(other)}' !")
            return False
        return self._route_container.load(other._route_container)

