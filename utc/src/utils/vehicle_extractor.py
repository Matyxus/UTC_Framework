from utc.src.constants.file_system.file_types.sumo_routes_file import SumoRoutesFile
from utc.src.constants.file_system.file_types.sumo_vehicles_file import SumoVehiclesFile
from utc.src.simulator.vehicle import Vehicle, VehicleEntry
from xml.etree.ElementTree import Element
from copy import deepcopy
from typing import Optional, Tuple, List


class VehicleExtractor:
    """
    Extracts vehicles from vehicle file, provides utility methods.
    """
    def __init__(self, vehicles_file: SumoVehiclesFile, routes_file: SumoRoutesFile):
        """
        :param vehicles_file:
        :param routes_file:
        """
        self.vehicles_file: SumoVehiclesFile = vehicles_file
        self.routes_file: SumoRoutesFile = routes_file
        # Memory of previously searched vehicles (end_time, index)
        self.previous_search: Tuple[float, int] = (0, 0)
        assert(self.vehicles_file is not None and self.vehicles_file.is_loaded() and self.vehicles_file.check_file())
        assert(self.routes_file is not None and self.routes_file.is_loaded())

    def estimate_arrival_naive(self, interval: Tuple[float, float]) -> Optional[VehicleEntry]:
        """
        :param interval: from which we want to extract vehicles
        :return: Dictionary mapping vehicle ids to vehicle, route and routes on graph (can be None),
        None if error occurred
        """
        # Retrieve vehicles that can make it in time, based on their depart time
        vehicles: Optional[List[Element]] = self.get_vehicles(interval)
        # print(f"Vehicles arriving in interval: {interval} -> {len(vehicles)}")
        if vehicles is None:
            print("Error at getting vehicles!")
            return None
        elif not vehicles:
            print(f"No vehicles found in interval: {interval}")
            return None
        entry: VehicleEntry = VehicleEntry(interval)
        [entry.add_vehicle(Vehicle(deepcopy(vehicle.attrib))) for vehicle in vehicles]
        routes_ids: List[str] = [vehicle.attrib["route"] for vehicle in vehicles]
        routes: List[Element] = self.routes_file.get_elements("route", set(routes_ids))
        if routes is None or len(routes) != len(set(routes_ids)):
            print("Error at getting routes")
            return None
        [entry.add_original_route(deepcopy(route)) for route in routes]
        return entry

    def get_vehicles(self, interval: Tuple[float, float]) -> Optional[List[Element]]:
        """
        Extracts vehicles from '.ruo.xml' file, filtered by start/end time as <start_time, end_time)

        :param interval: of vehicles arrival (earliest vehicle arrival, latest vehicle arrival (without))
        :return: List of vehicles represented by XML Element, None if error occurred
        """
        if not self.vehicles_file.has_vehicles():
            print(f"No vehicles in vehicle file: {self.vehicles_file}!")
            return None
        # Find if previous end_time is less than or equal to current start_time,
        # if so get saved index of last vehicle
        search_start: int = 0
        if self.previous_search is not None and self.previous_search[0] <= interval[0]:
            search_start = self.previous_search[1]  # Index
        # Vehicles
        vehicles: List[Element] = []
        for index, vehicle in enumerate(self.vehicles_file.root.findall("vehicle")[search_start:]):
            depart: float = float(vehicle.attrib["depart"])
            if interval[0] <= depart < interval[1]:
                vehicles.append(vehicle)
            elif depart >= interval[1]:
                self.previous_search = (interval[1], index)
                break
        return vehicles
