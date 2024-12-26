from utc.src.constants.file_system.my_file import MyFile
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, ElementTree, ParseError
from typing import Optional, List, Set


class XmlFile(MyFile):
    """
    Class handling xml type files
    """
    def __init__(self, file_path: str, mode: str = "r", extension: str = ""):
        self.tree: Optional[ElementTree] = None
        self.root: Optional[Element] = None
        super().__init__(file_path, mode, extension)  # Super call needs to happen after var declaration

    def load(self, file_path: str) -> bool:
        success: bool = super().load(file_path)
        if not success:
            print(f"Unable to initialize XML file: '{self.file_path}', file does not exist!")
            return False
        try:  # Check for parsing error
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
        except ParseError as e:
            print(
                f"Unable to parse xml file: {self.file_path}\n"
                f" got error: '{e}'\n, be sure the file is actually of type 'xml'!"
            )
            return False
        return True

    def save(self, file_path: str = "default") -> bool:
        file_path = (self.file_path if file_path == "default" else file_path)
        if self.root is None or self.tree is None:
            print(f"Error cannot save file: {file_path}, 'root' of xml file is of type: 'None' !")
            return False
        # Check extension
        if not file_path.endswith(self.extension):
            print(f"Expected default extension: '{self.extension}', got: '{file_path}' !")
            return False
        try:
            # tree = ET.ElementTree(self.tree)
            ET.indent(self.tree, space="\t", level=0)  # Et.indent is Python3.9 !
            self.tree.write(file_path, encoding="utf-8", xml_declaration=True)
        except OSError as e:
            print(f"Unable to save xml file: '{file_path}', got error: {e} !")
            return False
        # print(f"Successfully created file: '{file_path}'")
        return True

    # ------------------------------------------ Getters ------------------------------------------

    def get_elements(self, element_tag: str, element_ids: Set[str]) -> Optional[List[Element]]:
        """
        :param element_tag: tag of xml element object (must be first child of root)
        :param element_ids: ids of objects to extract
        :return: List of xml elements, None if error occurred
        """
        if not self.is_loaded():
            return None
        ret_val: List[Element] = [
            xml_element for xml_element in self.root.findall(element_tag)
            if xml_element.attrib["id"] in element_ids
        ]
        return ret_val

    # ------------------------------------------ Utils ------------------------------------------

    def is_loaded(self) -> bool:
        return super().is_loaded() and self.root is not None

    def get_known_path(self, file_name: str) -> str:
        raise NotImplementedError("Error, method 'get_known_path' must be implemented by subclasses of XmlFile class!")
