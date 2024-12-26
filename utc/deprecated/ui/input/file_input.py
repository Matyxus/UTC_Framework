from typing import Optional, Tuple
from utc.deprecated.ui.input.my_input import MyInput, stdin
from utc.deprecated.ui.input.input_utils import ArgumentValidator
from typing import List


class FileInput(MyInput):
    """
    Class representing methods used to read
    input from redirected file trough command line ('stdin')
    """

    def __init__(self):
        super().__init__()
        if not self.is_redirected():
            print(f"Error, input is not redirected from file, but class 'FileInput' was initialized!")

    def initialize_input(self) -> None:
        self.argument_validator = ArgumentValidator()

    def get_input(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Reads input from redirected file ('stdin') to this program

        :return: tuple containing (command name, string of command arguments)
        given by user or read from file, 'None' if an error occurred
        """
        if not self.is_redirected():
            print(f"Cannot read input from stdin, no file was redirected!")
            return None, None
        file_line: str = next(stdin, "").strip()
        # Skip comments from input files
        while file_line and file_line.startswith(";"):
            file_line = next(stdin, "").strip()
        split_input: List[str] = file_line.split()
        # End of input
        if not split_input:
            command_name = "exit"
            print("Reached end of file, returning command: 'exit'")
        else:
            print(f"Reading line: '{file_line}' from stdin")
            command_name = split_input.pop(0)
        return command_name, " ".join(split_input)

    # ------------------------------------------------ Utils ------------------------------------------------

    def is_initialized(self) -> bool:
        return self.argument_validator is not None
