from utc.src.constants.file_system.file_types.xml_file import XmlFile, Element
from utc.src.constants.static import FileExtension, FilePaths, DirPaths
from typing import List, Tuple, Union, Optional


class SumoConfigFile(XmlFile):
    """
    File class handling ".sumocfg" files, provides
    utility methods (setters, getters, ..)
    """
    def __init__(self, file_path: str = FilePaths.XmlTemplates.SUMO_CONFIG):
        """
        :param file_path: to ".sumocfg" file, can be name (in such case
        directories 'generated' & 'planned' in utc/data/scenarios/simulation
        will be search for corresponding file, default is template of ".sumocfg" file
        """
        super().__init__(file_path, extension=FileExtension.SUMO_CONFIG)

    def save(self, file_path: str = "default") -> bool:
        if not self.check_file():
            return False
        elif file_path == "default" and self.file_path == FilePaths.XmlTemplates.SUMO_CONFIG:
            print("Cannot overwrite template for '.sumocfg' files!")
            return False
        return super().save(file_path)

    # ------------------------------------------ Setters ------------------------------------------

    def set_network_file(self, network_path: str) -> bool:
        """
        :param network_path: sumo road network path to file ('.net.xml')
        :return: True on success, false otherwise
        """
        if self.get_file_name(network_path) == network_path or not (network_path.endswith(FileExtension.SUMO_NETWORK)):
            print(f"Error, expected full road network path, got: '{network_path}'")
            return False
        # Relative path also works against format string
        self.root.find("input").find("net-file").attrib["value"] = self.get_relative_path(
            network_path, DirPaths.SCENARIO_CONFIGS
        )
        return True

    def set_routes_file(self, routes_path: str) -> bool:
        """
        :param routes_path: path of routes file ('.rou.xml')
        :return: True on success, false otherwise
        """
        if self.get_file_name(routes_path) == routes_path or not (routes_path.endswith(FileExtension.SUMO_ROUTES)):
            print(f"Error, expected full routes path, got: '{routes_path}'")
            return False
        self.set_additional_file(routes_path)
        return True

    def set_additional_file(self, file_path: str) -> bool:
        """
        :param file_path: of file to be added
        :return: True on success, false otherwise
        """
        if self.get_file_name(file_path) == file_path:
            print(f"Error, expected full path to additional file, got: '{file_path}'")
            return False
        file_path = self.get_relative_path(file_path, DirPaths.SCENARIO_CONFIGS)
        if file_path in self.root.find("input").find("additional-files").attrib["value"]:
            print(f"File: {file_path} is already listed as additional file!")
            return False
        # Add first file, add ',' to name
        if self.root.find("input").find("additional-files").attrib["value"] != "":
            self.root.find("input").find("additional-files").attrib["value"] += "," + file_path
        else:
            self.root.find("input").find("additional-files").attrib["value"] = file_path
        return True

    def set_begin(self, time: Union[int, float]) -> bool:
        """
        :param time: starting time of simulation
        :return: True on success, false otherwise
        """
        self.root.find("time").find("begin").attrib["value"] = str(time)
        return True

    def set_end(self, time: Optional[Union[int, float]]) -> bool:
        """
        :param time: ending time of simulation (In case of None value, end time is removed)
        :return: True on success, false otherwise
        """
        if time is None:
            time_element: Element = self.root.find("time")
            time_element.remove(time_element.find("end"))
        else:
            self.root.find("time").find("end").attrib["value"] = str(time)
        return True

    def set_step_length(self, step: Union[int, float]) -> bool:
        """
        :param step: step length of simulation
        :return: True on success, false otherwise
        """
        # Add step-length element if it does not exist
        if self.root.find("time").find("step-length") is None:
            self.root.find("time").append(Element("step-length", {"value": ""}))
        self.root.find("time").find("step-length").attrib["value"] = str(step)
        return True

    def remove_additional_file(self, file_path: str) -> bool:
        """
        :param file_path:
        :return:
        """
        file_path = self.get_relative_path(file_path, DirPaths.SCENARIO_CONFIGS)
        if file_path in self.root.find("input").find("additional-files").attrib["value"]:
            self.root.find("input").find("additional-files").attrib["value"] = \
                self.root.find("input").find("additional-files").attrib["value"].replace("," + file_path, "")
            return True
        return False

    def add_routing(self) -> None:
        """
        :return:
        """
        if self.root.find("output") is None:
            self.root.append(Element("output"))
        output_element: Element = self.root.find("output")
        # Add routing components
        for routing_component in ["probability", "threads", "pre-period"]:
            if output_element.find(f"device.rerouting.{routing_component}") is None:
                output_element.append(Element(f"device.rerouting.{routing_component}", {"value": ""}))
        # Set values
        output_element.find("device.rerouting.probability").attrib["value"] = "1"
        output_element.find("device.rerouting.threads").attrib["value"] = "8"
        output_element.find("device.rerouting.pre-period").attrib["value"] = "30"
        return

    # ------------------------------------------ Getters ------------------------------------------

    def get_network(self) -> str:
        """
        :return: Full path to road network file set to this configuration file
        """
        return self.resolve_relative_path(
            self.dir_path, self.root.find("input").find("net-file").attrib["value"]
        )

    def get_routes_file(self) -> str:
        """
        :return:
        """
        return self.resolve_relative_path(
            self.dir_path, self.root.find("input").find("route-files").attrib["value"]
        )

    def get_routes(self) -> str:
        """
        :return: Full path to routes file set to this configuration file, Empty string if unable to be found
        """
        routes_path: str = ""
        # Find route file in additional files
        for file_path in self.get_additional_files():
            if file_path.endswith(FileExtension.SUMO_ROUTES):
                routes_path = file_path
                break
        # Unable to find
        if not routes_path:
            print(f"Unable to find routes file for config file: {self.file_path}")
            return ""
        return routes_path

    def get_additional_files(self) -> List[str]:
        """
        :return: List of full paths from additional files given to this configuration file
        """
        if not self.root.find("input").find("additional-files").attrib["value"]:
            return []
        return [
            self.resolve_relative_path(self.dir_path, additional_file) for additional_file in
            self.root.find("input").find("additional-files").attrib["value"].split(",")
        ]

    def get_start_time(self) -> int:
        """
        :return: Starting time of simulation (seconds)
        """
        return int(self.root.find("time").find("begin").attrib["value"])

    def get_end_time(self) -> int:
        """
        :return: Ending time of simulation (seconds)
        """
        return int(self.root.find("time").find("end").attrib["value"])

    def get_interval(self) -> Tuple[int, int]:
        """
        :return: start time and end time of simulation
        """
        return self.get_start_time(), self.get_end_time()


    def get_step_length(self) -> float:
        """
        :return: Step length of simulation (Default 1 second)
        """
        # Default
        if self.root.find("time").find("step-length") is None:
            return 1.0
        return float(self.root.find("time").find("step-length").attrib["value"])

    # ------------------------------------------ Utils ------------------------------------------

    def check_file(self) -> bool:
        """
        :return: True if file has correct structure and files used in <input> exist
        """
        # Checks ".sumocfg" file structure
        if self.tree is None:
            return False
        elif self.root is None:
            return False
        elif self.root.find("input") is None:
            print(f"Unable to find xml element <input> in file: '{self.file_path}' !")
            return False
        return True

    def get_known_path(self, file_name: str) -> str:
        # Does not exist, return original value
        return file_name
