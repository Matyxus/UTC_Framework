from xml.etree.ElementTree import Element
from typing import Dict, Union, Any


class XmlObject:
    """ Class representing xml objects """
    def __init__(self, tag: str, identifier: str, internal_id: int, attributes: Dict[str, str] = None):
        """
        :param tag: name of object
        :param identifier: id of objects (string)
        :param internal_id: internal id of objects (instance counter)
        :param attributes: of object
        """
        self.tag = tag
        self.id: str = identifier
        self.internal_id: int = internal_id
        self.attributes: Dict[str, str] = attributes

    # ------------------------------------- Utils -------------------------------------

    def get_id(self, internal: bool = False) -> Union[str, int]:
        """
        :param internal:
        :return:
        """
        return self.id if not internal else self.internal_id

    def get_attribute(self, attribute: str) -> Any:
        """
        :param attribute: name of attribute present in attributes dictionary
        :return: value associated with attribute name (None if it does not exist)
        """
        return self.attributes.get(attribute, None)

    def convert_attributes(self) -> Dict[str, str]:
        """
        :return: Attributes in correct format for Element object (string mapped to string)
        """
        return {key: str(value) for key, value in self.attributes.items()}

    def to_xml(self) -> Element:
        """
        :return: xml Element representing this object
        """
        return Element(self.tag, self.convert_attributes())

    def info(self, verbose: bool = True) -> str:
        """
        :param verbose: the detail of output
        :return: string representation of class
        """
        raise NotImplementedError("Error, method 'info' must be implemented by children of XmlObject")

    # ------------------------------------- Magic methods -------------------------------------

    def __hash__(self) -> int:
        """
        :return: Hash of attribute 'id'
        """
        return self.internal_id

    def __eq__(self, other: 'XmlObject') -> bool:
        """
        :param other: class to compare against self
        :return: true if classes are of same type and have same id, false otherwise
        """
        if other is None:
            return False
        return self.id == other.id

    def __lt__(self, other: 'XmlObject') -> bool:
        """
        :param other: object to compare with (subclass of XmlObject)
        :return: True if other object has lesser internal id, false otherwise
        """
        return self.internal_id < other.internal_id

    def __str__(self) -> str:
        """
        :return: string representation of xml object
        """
        return f"<{self.tag} {' '.join(['{0}={1}'.format(k, v) for k,v in self.attributes.items()])}/>"
