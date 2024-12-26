from utc.src.simulator.vehicle.generators.vehicle_generator import VehicleGenerator, Graph, Vehicle
from typing import Tuple, Iterator, Dict, List
import numpy as np


class VehicleFlows(VehicleGenerator):
    """ Class serving for generating vehicles """

    def __init__(self, graph: Graph = None, seed: int = 1):
        super().__init__(graph)
        np.random.seed(seed)
        # Type of flow mapped to expected value (number of seconds) per vehicle send
        self.flow_types: Dict[str, int] = {
            "light":  7,
            "medium": 5,
            "heavy":  3,
            "congested": 2
        }
        print("Initialized VehicleFlows")

    # -------------------------------------------- Interface --------------------------------------------

    def random_flow(
            self, from_junction_id: str, to_junction_id: str, minimal: int,
            maximal: int, period: int, start_time: int, end_time: int
            ) -> None:
        """
        Randomly generates between minimal and maximal cars every period, starting
        from start_time and ending at end_time.

        :param from_junction_id: starting junction of cars
        :param to_junction_id: destination junction of cars
        :param minimal: minimal amount of cars to be sent
        :param maximal: maximal amount of cars to be sent
        :param period: time (seconds) over which vehicles are sent
        :param start_time: of flow (seconds)
        :param end_time: of flow (seconds)
        :return: None
        """
        # ---------------------- Checks ----------------------
        if not self.check_args(from_junction_id, to_junction_id, start_time=start_time, end_time=end_time):
            return
        elif not maximal >= minimal:
            print(f"Expected argument 'maximal' to be higher or equal to 'minimal', got: {maximal} < {minimal} !")
            return
        elif not minimal >= 1:
            print(f"Expected arguments 'minimal' to be at least one, got: {minimal} !")
            return
        print("Generating random flow...")
        route_id: str = self.get_path(from_junction_id, to_junction_id)
        self.generators.append(self.generate_random_flow((minimal, maximal), period, route_id, (start_time, end_time)))

    def uniform_flow(
            self, from_junction_id: str, to_junction_id: str,
            vehicle_count: int, start_time: int, end_time: int,
            fluctuation: float = 0
            ) -> None:
        """
        :param from_junction_id: starting junction of cars
        :param to_junction_id: destination junction of cars
        :param vehicle_count: number of vehicles (equally spaced), might not be precise if
        fluctuation is used (on average it is)
        :param start_time: of flow (seconds)
        :param end_time: of flow (seconds)
        :param fluctuation: of flow (value between 0 & 1, taken as percentage)
        :return: None
        """
        # Check args
        if not self.check_args(from_junction_id, to_junction_id, vehicle_count, start_time, end_time):
            return
        elif fluctuation < 0 or fluctuation > 1:
            print(f"Fluctuation parameter must be value between 0 and 1, got: {fluctuation} !")
            return
        route_id: str = self.get_path(from_junction_id, to_junction_id)
        print("Generating uniform flow...")
        # Add fluctuation
        if fluctuation > 0:
            fluctuation = round(fluctuation, 2)
            periods: int = (end_time - start_time) // 20
            fluctuating_vehicles: int = int(vehicle_count * fluctuation) * 2
            vehicle_count -= fluctuating_vehicles // 2
            vehicle_interval: Tuple[int, int] = (0, max(fluctuating_vehicles // periods, 1))
            self.generators.append(self.generate_random_flow(vehicle_interval, 20, route_id, (start_time, end_time)))
        self.generators.append(self.generate_uniform_flow((start_time, end_time), route_id, vehicle_count))

    def exponential_flow(
            self, from_junction_id: str, to_junction_id: str,
            start_time: int, end_time: int, increase: float = 1
            ) -> None:
        """
        Generates flow depending on parameter 'flow_type',
        'light' sends (0-10)vehicles/minute -> 5 on average,
        'medium' sends (5-15) vehicles/minute -> ~8 on average,
        'heavy' sends (10-20) vehicles/minute -> 15 on average

        :param from_junction_id: starting junction of cars
        :param to_junction_id: destination junction of cars
        :param start_time: of flow (seconds)
        :param end_time: of flow (seconds)
        :param increase: rate of increase of flow -> till achieving maximum capacity
        (increases number of vehicles), must be higher than 0, default 1 (no increase)
        :return: None
        """
        # ---------------------- Checks ----------------------
        if not self.check_args(from_junction_id, to_junction_id, start_time=start_time, end_time=end_time):
            return
        elif (end_time - start_time) < 120:
            print(f"Duration of exponential flow has to be at least 120 seconds, got: {end_time-start_time}")
            return
        elif increase < 0:
            print(f"Parameter increase has to be higher than 0, got: {increase}")
            return
        route_id: str = self.get_path(from_junction_id, to_junction_id)
        print("Generating exponential flow...")
        self.generators.append(self.generate_exponential_flow((start_time, end_time), route_id, increase))

    # -------------------------------------------- Generators --------------------------------------------

    @staticmethod
    def generate_random_flow(
            vehicle_interval: Tuple[int, int], period: int,
            route_id: str, time_interval: Tuple[int, int]
            ) -> Iterator[Vehicle]:
        """
        :param vehicle_interval: minimal and maximal value of vehicles
        :param period: how often should vehicles be generated
        :param route_id: id of route used by vehicles
        :param time_interval: of vehicles arrival time (start_time, end_time)
        :return: Iterator of vehicles
        """
        starting_time: int = time_interval[0] - period
        ending_time: int = time_interval[0]
        # Generate random vehicle_counts N times (generating_time / period)
        episodes: int = int((time_interval[1] - time_interval[0]) / period)
        for vehicle_count in np.random.randint(vehicle_interval[0], vehicle_interval[1] + 1, episodes):
            starting_time += period
            ending_time += period
            # Generate random departing times for vehicles
            for depart_time in np.random.randint(starting_time, ending_time, vehicle_count):
                yield Vehicle(depart_time, route_id)

    @staticmethod
    def generate_uniform_flow(time_interval: Tuple[int, int], route_id: str, vehicle_count: int) -> Iterator[Vehicle]:
        """
        :param time_interval: of vehicles arrival time (start_time, end_time)
        :param route_id: id of route that cars will use
        :param vehicle_count: number of vehicles (equally spaced)
        :return: Iterator of vehicles
        """
        for depart_time in np.linspace(time_interval[0], time_interval[1], vehicle_count):
            yield Vehicle(round(depart_time, 2), route_id)

    def generate_exponential_flow(
            self, time_interval: Tuple[int, int],
            route_id: str, increase: float
            ) -> Iterator[Vehicle]:
        """
        :param time_interval: of vehicles arrival time (start_time, end_time)
        :param route_id: id of route that cars will use
        :param increase: rate of increase of flow (direct multiplier for number of vehicles),
        must be higher than 0, if equal to 1 -> no increase (default)
        :return: Iterator of vehicles
        """
        duration: int = time_interval[1] - time_interval[0]
        flow_time: int = int((1/3) * duration)
        half_time: int = int(0.5 * flow_time)
        current_time: Tuple[int, int] = (time_interval[0], time_interval[0] + flow_time)
        traffic_types: List[str] = list(self.flow_types.keys())
        for i in range(len(traffic_types)-1):
            current_flow: float = self.flow_types[traffic_types[i]] * increase
            next_flow: float = self.flow_types[traffic_types[i+1]] * increase
            # uniform flow
            yield from self.generate_uniform_flow(current_time, route_id, round(flow_time / current_flow))
            # Transition
            # Vehicle difference per second between flows, multiplied by duration of transition
            vehicle_diff: int = int(
                ((1 / next_flow) - (1 / current_flow)) * half_time
            )
            # Random flow to make transition between flows smoother
            yield from self.generate_random_flow(
                (vehicle_diff, vehicle_diff + 1), half_time, route_id, (current_time[0] + half_time, current_time[1])
            )
            # move time
            current_time = (current_time[1], current_time[1] + flow_time)

    # -------------------------------------------- Utils --------------------------------------------

    def get_methods(self) -> List[Tuple['VehicleGenerator', Dict[str, callable]]]:
        return [(self, {
            "random_flow": self.random_flow, "uniform_flow": self.uniform_flow,
            "exponential_flow": self.exponential_flow
        })]
