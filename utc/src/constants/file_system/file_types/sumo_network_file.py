from utc.src.constants.file_system.file_types.xml_file import XmlFile
from xml.etree.ElementTree import Element
from utc.src.constants.static import FileExtension, FilePaths
from typing import Iterator, Tuple, Optional


class SumoNetworkFile(XmlFile):
    """
    File class handling ".net.xml" files,
    provides utility methods
    """
    def __init__(self, file_path: str):
        """
        :param file_path: to ".net.xml" file, can be name (in such case
        directory utc/data/maps/osm  will be search for corresponding file)
        """
        super().__init__(file_path, extension=FileExtension.SUMO_NETWORK)

    # ------------------------------------------ Getters ------------------------------------------

    def get_junctions(self) -> Optional[Iterator[Element]]:
        """
        :return: generator of non-internal
        Junction xml elements, none if file is not loaded
        """
        # File is not loaded
        if not self.is_loaded():
            print(f"Xml file of sumo road network is not loaded, cannot return junctions!")
            return None
        # Find all xml elements named "junction"
        for junction in self.root.findall("junction"):
            # Filter internal junctions
            if ("type" in junction.attrib) and (junction.attrib["type"] != "internal"):
                yield junction

    def get_connections(self) -> Optional[Iterator[Element]]:
        """
        :return: generator of non-internal
        Connection xml elements, none if file is not loaded
        """
        # File is not loaded
        if not self.is_loaded():
            print(f"Xml file of sumo road network is not loaded, cannot return connections!")
            return None
        # Find all xml elements named "connection"
        for connection in self.root.findall("connection"):
            # Filter internal connections
            if connection.attrib["from"][0] != ":":
                yield connection

    def get_edges(self) -> Optional[Iterator[Element]]:
        """
        :return: generator of non-internal Edge xml elements, None if file is not loaded
        """
        # File is not loaded
        if not self.is_loaded():
            print(f"Xml file of sumo road network is not loaded, cannot return edges!")
            return None
        # Find all xml elements named "edge"
        for edge in self.root.findall("edge"):
            # Filter internal edges
            if not ("function" in edge.attrib):
                yield edge

    def get_lanes(self) -> Optional[Iterator[Element]]:
        """
        :return: generator of non-internal Edge xml elements, None if file is not loaded
        """
        # File is not loaded
        if not self.is_loaded():
            print(f"Xml file of sumo road network is not loaded, cannot return lanes!")
            return None
        # Iterate over all edges and yield lanes
        for edge in self.get_edges():
            yield from edge.findall("lane")

    def get_component_interval(self, component_type: str) -> Optional[Tuple[int, int]]:
        """
        :param component_type: either edge or junction
        :return: starting and ending index of non-internal objects in root (indexed as list)
        """
        if component_type not in {"edge", "junction"}:
            return None
        first_index: int = -1
        last_index: int = 0
        # Find first index
        for index, child in enumerate(self.root[:]):
            # Find the correct type and filter out internal objects
            if child.tag == component_type and child.attrib["id"][0] != ":":
                first_index = index
                break
        # Find last index
        for index, child in enumerate(self.root[first_index:]):
            if child.tag != component_type or child.attrib["id"][0] == ":":
                last_index = index + first_index - 1
                break
        return first_index, last_index

    def get_roundabouts(self) -> Optional[Iterator[Element]]:
        """
        :return: generator of non-internal
        Roundabout xml elements, none if file is not loaded
        """
        # File is not loaded
        if not self.is_loaded():
            print(f"Xml file of sumo road network is not loaded, cannot return roundabouts!")
            return None
        # Find all xml elements named "roundabout"
        yield from self.root.findall("roundabout")  # No need to check for internal

    # ------------------------------------------ Utils  -----------------------------------------

    def get_known_path(self, file_name: str) -> str:
        return FilePaths.MAP_SUMO.format(file_name)
