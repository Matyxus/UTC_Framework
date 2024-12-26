from utc.src.constants.file_system.file_types.xml_file import XmlFile, Element
from utc.src.constants.static import FileExtension, FilePaths
from typing import List


class SumoVehiclesFile(XmlFile):
    """
    File class handling vehicle files for SUMO, provides utility methods
    """
    def __init__(self, file_path: str = FilePaths.XmlTemplates.SUMO_VEHICLE):
        """
        :param file_path: to ".add.xml" file, can be name (in such case
        directory 'utc/data/scenarios/name/additional' will be search for corresponding file),
        default is template of ".rou.xml" file
        """
        super().__init__(file_path, extension=FileExtension.SUMO_ADDITIONAL)

    def save(self, file_path: str = "default") -> bool:
        if not self.check_file():
            return False
        elif file_path == "default" and self.file_path == FilePaths.XmlTemplates.SUMO_VEHICLE:
            print("Cannot overwrite template for 'vehicles' file!")
            return False
        return super().save(file_path)

    # ------------------------------------------ Adders ------------------------------------------

    def add_vehicle(self, vehicle: Element) -> bool:
        """
        :param vehicle: to be added to vehicles file
        :return: True on success, false otherwise
        """
        # Checks
        if vehicle is None:
            print("Cannot add vehicle of type None to routes file!")
            return False
        elif not self.check_vehicle(vehicle):
            return False
        self.root.append(vehicle)
        return True

    def add_vehicles(self, vehicles: List[Element]) -> bool:
        """
        :param vehicles: to be added to vehicles file
        :return: True on success, false otherwise
        """
        # Checks
        if not vehicles:
            print("Received empty list of vehicles!")
            return False
        elif not all([self.check_vehicle(vehicle) for vehicle in vehicles]):
            return False
        [self.root.append(vehicle) for vehicle in vehicles]
        return True

    # ------------------------------------------ Getters ------------------------------------------

    def get_start_time(self) -> float:
        """
        :return: First vehicle arrival time (-1 if no vehicles are found)
        """
        if not self.check_file():
            return -1
        elif not self.has_vehicles():
            print("No vehicles in routes file!")
            return -1
        return float(self.root.findall("vehicle")[0].attrib["depart"])

    def get_end_time(self) -> float:
        """
        :return: Last vehicle arrival time (-1 if no vehicles are found)
        """
        if not self.check_file():
            return -1
        elif not self.has_vehicles():
            print("No vehicles in routes file!")
            return -1
        return float(self.root.findall("vehicle")[-1].attrib["depart"])

    # ------------------------------------------ Utils  ------------------------------------------

    def has_vehicles(self) -> bool:
        """
        :return: True if there are any xml elements of tag "vehicle", false otherwise
        """
        return self.root.find("vehicle") is not None

    def check_file(self) -> bool:
        """
        :return: True if file has correct structure and files used in <input> exist
        """
        # Checks ".sumocfg" file structure
        if self.tree is None:
            print(f"XML Tree is None, cannot save RoutesFile!")
            return False
        elif self.root is None:
            print("XML root of Tree is None, cannot save RoutesFile!")
            return False
        elif self.root.find("vType") is None:
            print(f"Unable to find xml element <vType> in file: {self} !")
            return False
        return True

    def check_vehicle(self, vehicle: Element) -> bool:
        """
        :param vehicle: extracted from simulation, to be checked
        :return: True if vehicle has all needed attributes, false otherwise
        """
        if vehicle is None:
            print("Vehicle is of type None!")
            return False
        elif "id" not in vehicle.attrib:
            print(f"Vehicle: {vehicle} is missing attribute 'id' !")
            return False
        elif "route" not in vehicle.attrib:
            print(f"Vehicle: {vehicle} is missing attribute 'route' !")
            return False
        elif "type" not in vehicle.attrib:
            print(f"Vehicle: {vehicle} is missing attribute 'type' !")
            return False
        return True

    def get_known_path(self, file_name: str) -> str:
        # Scenario specific, return original file_name
        return FilePaths.SCENARIO_VEHICLES.format(file_name, file_name)
