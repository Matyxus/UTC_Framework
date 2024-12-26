from utc.src.constants.file_system import FilePaths, MyFile, JsonFile
from typing import Union, Dict, Any


class Parameter(JsonFile):
    """
    Super class for template classes using
    dictionary to save parameters into '.json' files
    """
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.objects: Dict[str, Any] = {}

    def add_object(self, object_name: str, data: Any) -> bool:
        """
        :param object_name: name of object
        :param data: to be added
        :return: true on success, false otherwise
        """
        if not self.is_serializable(data):
            return False
        self.objects[object_name] = data
        return True

    def load_data(self) -> Any:
        data: Any = super().load_data()
        if data is None:
            return None
        elif isinstance(data, dict):
            self.objects = data
            try:
                self.check_data()
            except NotImplementedError:
                return data
        else:
            print(f"Data read from {self.file_path} is not of type 'dictionary', got: '{type(data)}'")
        return data

    # --------------------------------------- Utils ---------------------------------------

    def check_data(self) -> bool:
        """
        Checks data loaded from json file

        :return: true on success, false otherwise
        """
        raise NotImplementedError("Error, method: 'check_data' must be implemented by children of Parameter!")
