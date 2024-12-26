from utc.src.simulator.vehicle.generators.vehicle_generator import VehicleGenerator, Graph, Vehicle
from typing import List, Tuple, Iterator, Dict
import numpy as np


class VehicleTrips(VehicleGenerator):
    """ Class serving for generating vehicles """

    def __init__(self, graph: Graph = None):
        super().__init__(graph)
        print("Initialized VehicleTrips")

    # -------------------------------------------- Interface --------------------------------------------

    def add_vehicles(self, from_junction_id: str, to_junction_id: str, amount: int, depart_time: int) -> None:
        """
        Creates cars and appends them to binary search tree (sorted by depart time),
        which will later get saved into '.ruo.xml' file.

        :param from_junction_id: starting junction of cars
        :param to_junction_id: destination junction of cars
        :param amount: number of cars to create (>0)
        :param depart_time: time of departure (>=0)
        :return: None
        """
        # Check arguments and route existence
        if not self.check_args(from_junction_id, to_junction_id, amount, depart_time):
            return
        route_id: str = self.get_path(from_junction_id, to_junction_id)
        print("Adding vehicles ...")
        self.generators.append(self.generate_vehicles(amount, depart_time, route_id))

    def random_trips(self, amount: int, start_time: int, end_time: int) -> None:
        """
        Calculates period (vehicles entering network per period) according to formula:
        period = (end_time-start_time) / (network_length / 1000) / vehicle_count,
        randomly selects starting/ending junction to create path vehicles will take.
        ! May take a while, depending on the network size (to find shortest paths) and
        the duration (end_time - start_time) -> number of generate vehicles = (end_time - start_time) / period

        :param amount: Number of vehicles used in formula to calculate period (vehicles/second)
        :param start_time: starting time of trips
        :param end_time: ending time of trips
        :return: None
        """
        # Check arguments and route existence
        if not self.check_args(amount=amount, start_time=start_time, end_time=end_time):
            return
        print("Generating random trips ...")
        self.generators.append(self.generate_random_trips((start_time, end_time), amount))

    # -------------------------------------------- Generators --------------------------------------------

    # noinspection PyMethodMayBeStatic
    def generate_vehicles(self, amount: int, depart_time: float, route_id: str) -> Iterator[Vehicle]:
        """
        Generates vehicles for "add_vehicles" method, does not check arguments!

        :param amount: number of cars to create (>0)
        :param depart_time: time of departure (>=0)
        :param route_id: id of route assigned to vehicles
        :return: iterator of vehicles
        """
        yield from [Vehicle(depart_time, route_id) for _ in range(amount)]

    def generate_random_trips(self, time_interval: Tuple[int, int], amount: int) -> Iterator[Vehicle]:
        """
        :param time_interval: of vehicles arrival time (start_time, end_time)
        :param amount: number of vehicles
        :return: iterator of vehicles
        """
        network_length: int = int(sum([
            edge.get_length() * edge.get_lane_count() for edge in self.graph.skeleton.edges.values()
        ]))
        duration: int = (time_interval[1] - time_interval[0])
        # Formula taken from SUMO random trips
        period: float = round(duration / (network_length / 1000) / amount, 3)
        # Pointers for random.choice (must be a list!)
        starting_junctions_ptr: List[str] = list(self.graph.skeleton.starting_junctions)
        ending_junctions_ptr: List[str] = list(self.graph.skeleton.ending_junctions)
        for i in range(int(duration / period)):
            # Randomly choose route
            route_id: str = ""
            while not route_id:
                route_id = self.get_path(
                    np.random.choice(starting_junctions_ptr),
                    np.random.choice(ending_junctions_ptr),
                    message=False
                )
            yield Vehicle(i * period, route_id)

    # -------------------------------------------- Utils --------------------------------------------

    def get_methods(self) -> List[Tuple['VehicleGenerator', Dict[str, callable]]]:
        return [(self, {"add_vehicles": self.add_vehicles, "random_trips": self.random_trips})]
