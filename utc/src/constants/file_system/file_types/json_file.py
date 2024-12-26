from utc.src.constants.file_system.my_file import MyFile
from utc.src.constants.static import FileExtension, FilePaths
from typing import Union, Optional, Any
import json


class JsonFile(MyFile):
    """
    Class representing ".json" files, provides utility methods
    """
    def __init__(self, file_path: str, mode: str = "r"):
        super().__init__(file_path, mode, FileExtension.JSON)

    def load_data(self) -> Optional[dict]:
        """
        :return: data loaded from '.json' file
        """
        if not self.file_exists(self):
            return None
        self.mode = "r"
        with self as json_file:
            # Error occurred, during reading
            if json_file is None:
                return None
            return json.load(json_file)

    def save(self, file_path: str = "default", data: Union[list, dict] = None) -> bool:
        file_path = (self.file_path if file_path == "default" else file_path)
        if not file_path.endswith(FileExtension.JSON):
            print(f"Expected: '{FileExtension.JSON}' for JSON file got: '{file_path}' !")
            return False
        elif not self.is_serializable(data):
            return False
        # Save file
        self.mode = "w"
        with self as json_file:
            if json_file is None:
                return False
            json.dump(data, json_file, indent=2)
        self.mode = "r"
        print(f"Successfully saved '.json' file: '{file_path}'")
        return True

    # --------------------------------------- Utils ---------------------------------------

    @staticmethod
    def is_serializable(data: Any) -> bool:
        """
        :param data: to be serialized into json
        :return: True if data can be serialized
        """
        if data is None:
            print("Data is of type 'None', cannot be serialized!")
            return False
        try:
            json.dumps(data)
        except (TypeError, OverflowError, RecursionError) as e:
            print(f"Error: {e}, unable to serialize data!")
            return False
        return True

    @staticmethod
    def load_config(config_name: str) -> Optional[dict]:
        """
        :param config_name: name of configuration file
        :return: Dictionary containing contests of JSON file, None if error occurred
        """
        # Load configuration file
        if config_name is None or not config_name:
            print(f"Invalid name of configuration file: '{config_name}'!")
            return None
        elif JsonFile.file_exists(FilePaths.CONFIG_FILE.format(config_name), message=False):
            config_name = FilePaths.CONFIG_FILE.format(config_name)
        config_file: JsonFile = JsonFile(config_name)
        if not config_file.is_loaded():
            print(f"Configuration file: '{config_name}' does not exist!")
            return None
        return config_file.load_data()

    def get_known_path(self, file_name: str) -> str:
        return file_name
