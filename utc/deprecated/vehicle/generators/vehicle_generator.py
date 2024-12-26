from utc.src.simulator.vehicle.vehicle import Vehicle
from utc.src.graph.network.components import Route
from utc.src.graph import Graph
from typing import Dict, List, Tuple, Iterator


class VehicleGenerator:
    """ SuperClass for generating vehicles, provides utility methods """

    def __init__(self, graph: Graph = None):
        """
        :param graph: Graph for generating routes, default None
        """
        # -------------- Graph --------------
        self.graph: Graph = graph
        # Recording found shortest paths
        self.recorded_paths: Dict[str, Dict[str, str]] = {
            # from_junction_id : {to_junction_id : route_id, ...}, ...
        }
        # -------------- Routes & vehicles --------------
        self.routes: List[Route] = []
        self.generators: List[Iterator[Vehicle]] = []

    # ------------------------------------------ Utils  ------------------------------------------

    def get_path(self, from_junction_id: str, to_junction_id: str, message: bool = True) -> str:
        """
        :param from_junction_id: starting junction
        :param to_junction_id: destination junction
        :param message: bool (true/false) to print "invalid route" if route is not found
        :return: id of route, None if it does not exist
        """
        assert (self.graph is not None)
        if from_junction_id in self.recorded_paths and to_junction_id in self.recorded_paths[from_junction_id]:
            return self.recorded_paths[from_junction_id][to_junction_id]  # Get route from already found routes
        path: Route = self.graph.shortest_path.a_star(from_junction_id, to_junction_id)[1]
        # Record path
        if from_junction_id not in self.recorded_paths:
            self.recorded_paths[from_junction_id] = {}
        # Path doesnt exist, record its non existence with empty string
        if path is None:
            if message:
                print(f"Path between {from_junction_id} and {to_junction_id} does not exist!")
            self.recorded_paths[from_junction_id][to_junction_id] = ""
            return ""
        # Adds "s" for "shortest", avoids conflict in pddl
        path.attributes["id"] = ("s" + path.attributes["id"])
        self.recorded_paths[from_junction_id][to_junction_id] = path.attributes["id"]
        self.routes.append(path)
        return path.attributes["id"]

    def merge(self, other: 'VehicleGenerator') -> None:
        """
        Merges other VehicleGenerator subclass with current one, by
        changing pointers of objects to reference this class

        :param other: VehicleGenerator subclass
        :return: None
        """
        if not isinstance(other, VehicleGenerator):
            print(f"Expected other to be of type: 'VehicleGenerator', got: {type(other)} !")
            return
        other.graph = self.graph
        other.recorded_paths = self.recorded_paths
        other.routes = self.routes
        other.generators = self.generators

    def get_methods(self) -> List[Tuple['VehicleGenerator', Dict[str, callable]]]:
        """
        :return: tuple containing class to which methods belong to and
        dictionary mapping method name to function which generates vehicles,
        implemented by children of VehicleGenerator class
        """
        raise NotImplementedError("Method: 'get_methods' must be implemented by children of VehicleGenerator !")

    def check_args(
            self, from_junction_id: str = "", to_junction_id: str = "",
            amount: int = 1, start_time: float = 0, end_time: float = 1
            ) -> bool:
        """
        :param from_junction_id:
        :param to_junction_id:
        :param amount:
        :param start_time:
        :param end_time:
        :return:
        """
        if self.graph is None:
            print("Graph set to VehicleGenerator is of type 'None'!")
            return False
        # Check if path exists (only if from_junction and to_junction were given)
        elif from_junction_id and to_junction_id and not self.get_path(from_junction_id, to_junction_id):
            return False
        elif amount < 1:  # Check number of vehicles
            print(f"Number of cars cannot be lower than 1, got: {amount} !")
            return False
        elif start_time < 0:  # Check arrival time of vehicles
            print(f"Arrival time of vehicles cannot be lower than 0, got: {start_time} !")
            return False
        elif end_time < start_time:  # Check end time of vehicles (flows)
            print(f"Ending time cannot be lower than start time, got: {end_time} < {start_time}")
            return False
        return True
