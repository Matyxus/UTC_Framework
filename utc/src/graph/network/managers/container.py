from utc.src.utils.xml_object import XmlObject
from copy import deepcopy
from typing import Union, TypeVar, Generic, Iterable, Dict, List, Optional


class Container:
    """
    Class holding objects forming graph (e.g. Junction, Edges, Routes, ...) and their mappings,
    provides utility methods for object adding, removing, ...
    """
    _T = TypeVar('_T', bound=XmlObject)
    _O = Union[str, int, _T]

    def __init__(self, obj_type: Generic[_T], objects: Dict[str, _T]):
        """
        :param obj_type: types of object container holds
        :param objects: dictionary mapping original object ids to class instances
        """
        if not issubclass(obj_type, XmlObject):
            raise TypeError(f"Expected parameter 'object_type' to be subclass of 'Figure', got: {obj_type}")
        # References to objects contained in this Container
        self.object_type = obj_type
        self.objects: Dict[str, obj_type] = objects
        self.internal_objects: Dict[int, str] = {}

    def add_object(self, obj: _T, replace: bool = False) -> bool:
        """
        :param obj: to be added
        :param replace: True if object should be replaced (in case it already exists), False by default
        :return: True on success, false otherwise
        """
        if self.object_exists(obj, False) and not replace:
            print(
                f"Object '{type(obj)}' with id: '{obj.get_id(False)}'"
                f" cannot be added, since replace is set to False!"
            )
            return False
        self.objects[obj.get_id(internal=False)] = obj
        self.internal_objects[obj.get_id(internal=True)] = obj.get_id(internal=False)
        # print(f"Added object: {obj}")
        return True

    def remove_object(self, obj: _O) -> bool:
        """
        :param obj: to be removed
        :return: True on success, false otherwise
        """
        # Check for existence
        obj: Optional[Container._T] = self.get_object(obj)
        if obj is None:
            return False
        self.objects.pop(obj.get_id(internal=False))
        self.internal_objects.pop(obj.get_id(internal=True))
        return True

    def object_exists(self, obj: _O, message: bool = True) -> bool:
        """
        :param obj: id (internal or original) of object or class instance
        :param message: True if message about missing object should be printed, True by default
        :return: True if object exists, false otherwise
        """
        msg: str = ""
        ret_val: bool = True
        if isinstance(obj, str):
            if obj not in self.objects:
                msg = f"Unable to find object: {self.object_type} with original id: '{obj}'!"
                ret_val = False
        elif isinstance(obj, int):
            if obj not in self.internal_objects:
                msg = f"Unable to find object: {self.object_type} with internal id: '{obj}'!"
                ret_val = False
        elif isinstance(obj, self.object_type):
            mapped_object: Optional[Container._T] = self.objects.get(obj.get_id(internal=False), None)
            if mapped_object is None or mapped_object != obj:
                msg = f"Incorrect mapping of object: {self.object_type} with id: '{obj.get_id(internal=False)}'!"
                ret_val = False
        else:
            msg = f"Incorrect type of object, expected one of [str, int, {self.object_type}], got: '{type(obj)}'"
            ret_val = False
        # Print message
        if message and msg:
            print(msg)
        return ret_val

    def get_objects(self, objects: Iterable[_O], message: bool = True, filter_none: bool = False) -> List[Optional[_T]]:
        """
        :param objects: of graph (string - original, or int for internal representation)
        :param message: True if message about missing object should be printed, True by default
        :param filter_none: True if None values should be filtered out of list, False by default
        :return: List of Object instances (Some can be None if any given object does not exist)
        """
        ret_val: List[Optional[Container._T]] = [self.get_object(obj, message) for obj in objects]
        if filter_none:
            return [obj for obj in ret_val if obj is not None]
        return ret_val

    def get_object(self, obj: _O, message: bool = True) -> Optional[_T]:
        """
        :param obj: of graph (string - original, or int for internal representation)
        :param message: True if message about missing object should be printed, True by default
        :return: Object instance, None if object with given id does not exist
        """
        # Check, return based on type
        if not self.object_exists(obj, message):
            return None
        elif isinstance(obj, str):
            return self.objects[obj]
        elif isinstance(obj, self.object_type):
            return obj
        return self.objects[self.internal_objects[obj]]

    def load(self, other: 'Container') -> bool:
        """
        :param other: Container class
        :return: True on success, false otherwise.
        """
        # Checks
        if not isinstance(other, Container):
            print(f"Cannot load container from other objects, got: '{type(other)}' !")
            return False
        elif self.object_type != other.object_type:
            print("Cannot load different Container types !")
            print(f"{self.object_type} vs {other.object_type}")
            return False
        self.objects.clear()
        self.internal_objects.clear()
        # Add new items to dicts (dicts are references to Managers having this Container!)
        for obj_id, obj in other.objects.items():
            self.objects[obj_id] = deepcopy(obj)
        for internal, original in other.internal_objects.items():
            self.internal_objects[internal] = original
        return True
