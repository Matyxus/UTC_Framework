from utc.deprecated.ui.command import Command
from utc.deprecated.ui.input.input_utils import InputUtils
from prompt_toolkit.validation import ValidationError
from typing import Tuple, List, Dict, Optional, Any
from os import fstat
from sys import stdin, argv
from stat import S_ISREG


class MyInput(InputUtils):
    """
    Super class for classes working with input
    """
    def __init__(self):
        super().__init__()
        self.commands: Dict[str, Command] = {
            # command_name : Command
        }

    def initialize_input(self) -> None:
        """
        Initializes additional utility classes for input

        :return: None
        """
        raise NotImplementedError("Error, method: 'initialize_input' must be initialized by children of MyInput !")

    def get_input(self) -> Tuple[Optional[str], Optional[str]]:
        """
        :return: tuple containing (command name, list of command args string)
        given by user or read from file, 'None' if an error occurred
        """
        raise NotImplementedError("Error, method: 'get_input' must be initialized by children of MyInput !")

    def convert_args(self, command_name: str, arguments: str) -> Optional[List[Any]]:
        """
        :param command_name: read from file or given from user
        :param arguments: read from file or given from user
        :return: list of arguments converted to their values (sorted in order)
        """
        converted_args: Optional[List[Any]] = None
        # Checks
        if not arguments:
            return []
        elif not self.command_exists(command_name, message=True):
            return converted_args
        elif self.argument_validator is None:
            print(f"Argument validator is not initialized, cannot convert argments!")
            return converted_args
        self.argument_validator.set_command(self.commands.get(command_name, None))
        # Convert
        try:
            converted_args = self.argument_validator.convert_args(
                self.argument_validator.parse_input(arguments), arguments
            )
        except ValidationError as e:
            print(f"Error: {e.message}")
            return converted_args
        return converted_args

    # --------------------------------------------- Command Utils ---------------------------------------------

    def add_command(self, commands: List[Command], message: bool = False) -> None:
        """
        Adds command (or multiple) to data structure, fails if command name
        already exists

        :param commands: list of Command classes to be added
        :param message: if message about command already existing should be printed (default false)
        :return: None
        """
        for command in commands:
            # Check for existence
            if self.command_exists(command.name, message=message):
                continue
            self.commands[command.name] = command
            print(f"Enabling new command: '{command.name}'")
        # Update command completer
        if self.command_completer is not None:
            self.command_completer.words = list(self.commands.keys())

    def remove_command(self, command_names: List[str], message: bool = False) -> None:
        """
        Adds command to data structure, fails if command name
        already exists

        :param command_names: list of command names to be removed
        :param message: if message about command not existing should be printed (default false)
        :return: None
        """
        for command_name in command_names:
            # Check for existence
            if not self.command_exists(command_name, message=message):
                continue
            del self.commands[command_name]
            print(f"Removing command: '{command_name}'")
        # Update command completer
        if self.command_completer is not None:
            self.command_completer.words = list(self.commands.keys())

    def command_exists(self, command_name: str, message: bool = False) -> bool:
        """
        :param command_name: to be checked for existence
        :param message: if message about command not existing should be printed, false by default
        :return: true if command name is already in use, false otherwise
        """
        ret_val: bool = command_name in self.commands
        if message and not ret_val:
            print(f"Command name with name: '{command_name}' does not exists, failed to remove!")
        return ret_val

    # --------------------------------------------- Utils ---------------------------------------------

    @staticmethod
    def get_argv() -> List[str]:
        """
        :return: argv arguments given to program
        """
        return argv

    @staticmethod
    def is_redirected() -> bool:
        """
        :return: true if input is redirected from file, false otherwise
        """
        mode: int = fstat(stdin.fileno()).st_mode
        return S_ISREG(mode)
