from utc.src.constants.file_system.file_types.xml_file import XmlFile, Element
from utc.src.constants.static import FileExtension, FilePaths
from typing import Optional, Dict, List


class SumoRoutesFile(XmlFile):
    """
    File class handling ".rou.xml" files, provides utility methods
    """

    def __init__(self, file_path: str = FilePaths.XmlTemplates.SUMO_ROUTES):
        """
        :param file_path: to ".rou.xml" file, can be name (in such case
        directory 'utc/data/scenarios/routes' will be search for corresponding file),
        default is template of ".rou.xml" file
        """
        super().__init__(file_path, extension=FileExtension.SUMO_ROUTES)
        # Recording of routes based on their edges to new id
        self.route_map: Dict[str, str] = {}
        # Counter for new route ids
        self.route_counter: int = 0

    def save(self, file_path: str = "default") -> bool:
        if file_path == "default" and self.file_path == FilePaths.XmlTemplates.SUMO_ROUTES:
            print(f"Cannot overwrite template for 'routes' file!")
            return False
        self.route_map.clear()
        return super().save(file_path)

    # ------------------------------------------ Adders ------------------------------------------

    def add_route(self, route: Element, re_index: bool = True) -> Optional[str]:
        """
        :param route: to be added to routes file
        :param re_index: if routes should be re-indexed (to avoid duplicates), True by default
        :return: New id of route, None if error occurred
        """
        # Checks
        if route is None:
            print(f"Cannot add route of type None to routes file!")
            return None
        elif not self.check_route(route):
            return None
        elif not re_index:
            self.root.append(route)
            return None
        # Record and add new route
        elif route.attrib["edges"] not in self.route_map:
            self.route_map[route.attrib["edges"]] = f"r{self.route_counter}"
            route.attrib["id"] = f"r{self.route_counter}"
            self.route_counter += 1
            self.root.append(route)
        return self.route_map[route.attrib["edges"]]

    def add_routes(self, routes: List[Element], re_index: bool = True) -> Optional[Dict[str, str]]:
        """
        :param routes: to be added to routes file
        :param re_index: if routes should be re-indexed (to avoid duplicates), True by default
        :return: Mapping of old route ids to new ids, None if error occurred
        """
        # Checks
        if not routes:
            return None
        elif not all([self.check_route(route) for route in routes]):
            return None
        return {route.attrib["id"]: self.add_route(route, re_index) for route in routes}

    # ------------------------------------------ Utils  ------------------------------------------

    def check_route(self, route: Element) -> bool:
        """
        :param route: extracted from simulation, to be checked
        :return: True if route has all needed attributes, false otherwise
        """
        if route is None:
            print(f"Route is of type None!")
            return False
        elif "id" not in route.attrib:
            print(f"Route: {route} is missing attribute 'id' !")
            return False
        elif "edges" not in route.attrib:
            print(f"Route: {route} is missing attribute 'edges' !")
            return False
        return True

    def get_known_path(self, file_name: str) -> str:
        # Scenario specific, return original file_name
        return FilePaths.SCENARIO_ROUTES.format(file_name, file_name)


# For testing purposes
if __name__ == "__main__":
    pass
