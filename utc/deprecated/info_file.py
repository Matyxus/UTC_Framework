from utc.src.constants.file_system.my_file import MyFile
from utc.src.constants.static import FileExtension
from typing import List, Dict, Tuple, Optional


class InfoFile(MyFile):
    """
    Class representing files containing commands and their arguments
    inputted by user (either dynamically or statically), default extension
    is ".info"
    """

    def __init__(self, file_path: str, mode: str = "w+"):
        super().__init__(file_path, mode, FileExtension.INFO)
        self.commands: List[Tuple[str, str]] = []

    # ------------------------------------ save & load ------------------------------------

    def save(self, file_path: str = "default", commands: List[Tuple[str, str]] = None) -> bool:
        """
        :param file_path: target file path (default is currently set one)
        :param commands: to be saved, none by default (currently set ones will be used)
        :return: true on success, false otherwise
        """
        if file_path != "default":
            self.file_path = file_path
        if not self.file_path.endswith(self.extension):
            print(
                f"For Info file expected extension to be: '{self.extension}'"
                f", got: '{file_path}' !"
            )
            return False
        elif not self.commands and commands is None:
            print(f"Currently set and given commands are empty, cannot save info file: '{self}'")
            return False
        # Save file
        self.mode = "w+"
        with self as info_file:
            if info_file is None:
                return False
            commands = commands if commands is not None else self.commands
            for command_name, command_args in commands:
                info_file.write(command_name + " " + command_args + "\n")
        print(f"Successfully saved '{self.extension}' file: '{self.file_path}'")
        return True

    def load_data(self) -> Tuple[Optional[List[str]], Optional[Dict[str, List[str]]]]:
        """
        :return: tuple (list of commands name, in order they are in file,
        dictionary mapping command name to list of its used arguments)
        """
        ret_val: Tuple[List[str], Dict[str, List[str]]] = ([], {})
        self.mode = "r"
        with self as info_file:
            if info_file is None:
                return None, None
            for line in info_file:
                line = line.rstrip().split(" ", 1)
                if not line:  # Empty line
                    continue
                elif len(line) < 1:
                    print(f"Expected info file to have: 'command_name'[space](optional - arguments).., got: {line}")
                    continue
                command_name: str = line[0]
                ret_val[0].append(command_name)
                if command_name not in ret_val[1]:
                    ret_val[1][command_name] = []
                ret_val[1][command_name].append(line[1] if len(line) > 1 else "")
        return ret_val

    def get_known_path(self, file_name: str) -> str:
        return file_name  # No default path


# For testing purposes
if __name__ == "__main__":
    temp: InfoFile = InfoFile("12_27_34_Sydney")
    val1, val2 = temp.load_data()
    print(val1, val2)

