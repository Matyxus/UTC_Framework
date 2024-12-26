from utc.src.utils.xml_object import XmlObject
from typing import Dict


class Vehicle(XmlObject):
    """ Class representing vehicle for SUMO """
    # https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html
    _counter: int = 0  # Variable serving to count number of class instances (to assign id's to vehicles)

    def __init__(self, attributes: Dict[str, str]):
        """
        :param attributes: time of vehicle
        """
        assert("id" in attributes)
        super().__init__("vehicle", attributes["id"], Vehicle._counter, attributes)
        Vehicle._counter += 1

    # -------------------------------- Setters --------------------------------

    def set_route(self, route_id: str) -> None:
        """
        :param route_id: id of route trough which cars will travel (must be defined in routes.route.xml file !)
        :return: None
        """
        self.attributes["route"] = route_id

    def set_depart(self, depart_time: float) -> None:
        """
        :param depart_time: time after which vehicle/s should arrive (seconds), 2 digit precision
        :return: None
        """
        self.attributes["depart"] = ("" if depart_time < 0 else str(round(depart_time, 2)))

    # -------------------------------- Getters --------------------------------

    def get_depart(self) -> float:
        """
        :return: time of vehicle depart, 2 digit precision (used for sorting), raises error if attribute is not set!
        """
        return float(self.attributes["depart"])

    # -------------------------------- Utils --------------------------------

    def info(self, verbose: bool = True) -> str:
        return str(self)

    # -------------------------------- Magics --------------------------------

    def __lt__(self, other: 'Vehicle') -> bool:
        if isinstance(other, Vehicle):
            return self.get_depart() < other.get_depart()
        return False
