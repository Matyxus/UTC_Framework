from utc.src.utils.xml_object import XmlObject
from utc.src.graph.network.parts.route import Route
from typing import Dict, Tuple, Set, List, Optional


class Junction(XmlObject):
    """
    Class representing junction from SUMO network '.net.xml' file,
    contains mapping of incoming routes to outgoing routes
    (If incoming is of type 'None' Junction is starting)
    """
    def __init__(self, attributes: Dict[str, str], internal_id: int):
        """
        :param attributes: extracted from xml element
        :param internal_id: internal identifier of object
        """
        super().__init__("junction", attributes.pop("id"), internal_id, attributes)
        self.x: float = round(float(attributes["x"]), 2)
        self.y: float = round(float(attributes["y"]), 2)
        self.traffic_lights: bool = ("traffic_light" == attributes["type"])
        self.connections: Dict[Optional[Route], List[Route]] = {}

    # --------------------------------------------- Connections ---------------------------------------------

    def add_connection(self, from_route: Optional[Route], out_route: Optional[Route]) -> bool:
        """
        :param from_route: incoming route to this node (its id)
        :param out_route: route going from this node (if we came into junction using from_route)
        :return: True on success, false otherwise
        """
        # Check types
        if from_route is None and out_route is None:
            print(f"Cannot add connection to junction: '{self.id}' of both type 'None' !")
            return False
        # Add incoming route
        if from_route not in self.connections:
            self.connections[from_route] = []
        # Add outgoing route (avoid duplicates)
        if out_route is not None and not self.connection_exists(from_route, out_route, False):
            self.connections[from_route].append(out_route)
        return True

    def remove_connection(self, from_route: Optional[Route], out_route: Route) -> bool:
        """
        :param from_route: incoming route (can be 'None')
        :param out_route: outgoing route
        :return: True if connection was removed, false otherwise
        """
        if not self.connection_exists(from_route, out_route):
            return False
        self.connections[from_route].remove(out_route)
        return True

    def connection_exists(self, from_route: Optional[Route], out_route: Optional[Route], message: bool = True) -> bool:
        """
        :param from_route: incoming route (can be None, if 'out_route' is not)
        :param out_route: outgoing route (can be None, if 'from_route' is not)
        :param message: True if message about missing connection should be printed, default True
        :return: True if route exists in connections, false otherwise
        """
        # Check correct type
        ret_val: bool = True
        msg: str = ""
        if from_route is None and out_route is None:
            msg = "Either 'from_route' or 'out_route' argument can be of type None, not both!"
            ret_val = False
        elif from_route is not None:
            if from_route not in self.connections:
                msg = f"For junction: '{self.get_id()}', there is no incoming route: '{from_route.get_id()}' !"
                ret_val = False
            if out_route is not None and out_route not in self.connections[from_route]:
                msg = (
                    f"For junction: '{self.get_id()}', there is no connection between "
                    f"routes: '{from_route.get_id()}' -> '{out_route.get_id()}'!"
                )
                ret_val = False
        elif out_route not in self.get_out_routes():
            msg = f"For junction: '{self.get_id()}', there is no outgoing route: '{out_route.get_id()}' !"
            ret_val = False
        # Print message
        if message and msg:
            print(msg)
        return ret_val

    def remove_in_route(self, route: Optional[Route]) -> bool:
        """
        :param route: incoming route to be removed, can be of type 'None' for starting junctions
        :return: True if incoming route was removed, false otherwise
        """
        # Check
        if route not in self.connections:
            print(f"Cannot remove incoming route: {route} for junction: {self.id}, route does not exist!")
            return False
        self.connections.pop(route)
        return True

    def remove_out_route(self, route: Route) -> bool:
        """
        :param route: outgoing route to be removed (from all incoming routes)
        :return: True if outgoing route was removed, false otherwise
        """
        if route not in self.get_out_routes():
            print(f"Cannot remove outgoing route: {route} for junction: {self.id}, route does not exist!")
            return False
        for in_route, out_routes in self.connections.items():
            if route in out_routes:  # Remove mapping from all lists of outgoing routes
                out_routes.remove(route)
        # Check if 'None' route as out-going junctions, if not, remove it
        if self.is_starting() and not self.connections[None]:
            self.remove_in_route(None)
        return True

    def replace_in_route(self, in_route: Optional[Route], new_in_route: Optional[Route]) -> bool:
        """
        :param in_route: to be replaced
        :param new_in_route: replacing
        :return: True if connection was added, false otherwise
        """
        # Check types
        if in_route is None and new_in_route is None:
            print(f"Cannot replace incoming route to junction: '{self.id}' of both type 'None' !")
            return False
        elif in_route not in self.connections:
            print(f"Cannot replace incoming route: {in_route} in junction: {self.id}, route does not exist!")
            return False
        # Already exists, remove duplicates
        if new_in_route in self.connections:
            self.connections[new_in_route] += self.connections.pop(in_route)
            self.connections[new_in_route] = list(set(self.connections[new_in_route]))
        else:
            self.connections[new_in_route] = self.connections.pop(in_route)
            # Only add new connections if its not 'None' with no out-going rotes
            if new_in_route is None and not self.connections[new_in_route]:
                self.remove_in_route(new_in_route)
        return True

    # --------------------------------------------- Getters ---------------------------------------------

    def get_position(self) -> Tuple[float, float]:
        """
        :return: Tuple containing (x, y) coordinates
        """
        return self.x, self.y

    def get_in_routes(self) -> List[Route]:
        """
        :return: List of incoming routes (without 'None')
        """
        if None in self.connections:
            return list(self.connections.keys() ^ {None})
        return list(self.connections.keys())

    def get_out_routes(self) -> List[Route]:
        """
        :return: List of all out coming routes
        """
        return [route for route_list in self.connections.values() for route in route_list]

    def get_routes(self) -> List[Route]:
        """
        :return: List of all routes in junction (without 'None')
        """
        return self.get_in_routes() + self.get_out_routes()

    def get_in_neighbours(self) -> Set[str]:
        """
        :return: Set of previous neighbour junctions
        """
        return set([route.get_start() for route in self.get_in_routes()])

    def get_out_neighbours(self) -> Set[str]:
        """
        :return: Set of reachable neighbour junctions
        """
        return set([route.get_destination() for route in self.get_out_routes()])

    def get_neighbours(self) -> Set[str]:
        """
        :return: Set of neighbouring junctions id's
        """
        return self.get_in_neighbours() | self.get_out_neighbours()

    # --------------------------------------------- Utils ---------------------------------------------

    def is_starting(self) -> bool:
        """
        :return: True if junction is starting (has one incoming route of type 'None')
        """
        return None in self.connections

    def is_ending(self) -> bool:
        """
        :return: True if junction is ending (has at least one incoming route leading to no other)
        """
        return any((len(self.connections[in_route]) == 0) for in_route in self.connections.keys())

    def is_traffic_light(self) -> bool:
        """
        :return: True if junction has traffic lights, false otherwise
        """
        return self.traffic_lights

    def travel(self, from_route: Optional[Route]) -> Optional[List[Route]]:
        """
        :param from_route: one of incoming routes, if equal to None, returns all routes
        :return: list of outgoing routes, None if route is not incoming to this Junction
        """
        if from_route is None and not self.is_starting():
            print(f"Junction: {self.id} received 'None' as incoming junction but is not starting !")
            return self.get_out_routes()
        elif from_route not in self.connections:
            print(f"Junction: {self.id} does not contain incoming route: {from_route}!")
            return None
        return self.connections[from_route]

    def info(self, verbose: bool = True) -> str:
        ret_val: str = f"Junction: {self.id}({self.internal_id})\n"
        ret_val += f"Incoming routes: {len(self.get_in_routes())}, outgoing: {len(self.get_out_routes())}"
        if not verbose:
            return ret_val
        for incoming_route in self.connections.keys():
            ret_val += f"\n|-- {incoming_route.info() if incoming_route is not None else None}\n"
            for out_route in self.connections[incoming_route]:
                ret_val += f"\t|-- {out_route.info()}\n"
        return ret_val

    # --------------------------------------------- Magics ---------------------------------------------

    def __or__(self, other: 'Junction') -> 'Junction':
        """
        Merges with another junction (of same attributes), but with different connections

        :param other: Junction class
        :return: Current node merged with another
        :raises: TypeError if parameter 'other' is not Junction class
        """
        # Check
        if not isinstance(other, Junction):
            raise TypeError(f"Cannot compare classes: 'Junction' with '{type(other)}' !")
        for in_route, out_routes in other.connections.items():
            if in_route not in self.connections:  # Add new mapping
                self.connections[in_route] = out_routes
            else:  # Merge out_routes
                for out_route_id in out_routes:
                    if out_route_id not in self.connections[in_route]:
                        self.connections[in_route].append(out_route_id)
        return self

    def __ror__(self, other: 'Junction') -> 'Junction':
        """
        :param other: Junction class
        :return: Current node merged with another
        """
        return self.__or__(other)

