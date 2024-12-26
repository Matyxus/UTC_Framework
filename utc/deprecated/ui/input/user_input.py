from utc.deprecated.ui.command import Command
from utc.deprecated.ui.input.my_input import MyInput
from utc.deprecated.ui.input.input_utils import ArgumentValidator, InMemoryHistory, WordCompleter, Validator
from typing import Tuple, Optional, Union
from prompt_toolkit import prompt


class UserInput(MyInput):
    """
    Class representing input given by user dynamically from command line
    """

    def __init__(self):
        super().__init__()

    def initialize_input(self) -> None:
        """
        Initializes additional utility classes for input

        :return: None
        """
        self.argument_validator = ArgumentValidator()
        self.command_history = InMemoryHistory()
        self.command_completer = WordCompleter(list(self.commands.keys()), ignore_case=True, WORD=True)
        self.command_validator = Validator.from_callable(
            self.command_exists,
            error_message="This is command does not exist, for list of commands type 'help'!",
        )

    # --------------------------------------------- Input ---------------------------------------------

    def get_input(self) -> Tuple[Optional[str], Optional[str]]:
        """
        :return: tuple containing (command name, list of command args as string)
        given by user or read from file, 'None' if an error occurred
        """
        # Get input from user
        command_name: Optional[str] = self.ask_command_name()
        return command_name, self.ask_command_args(command_name)

    def ask_command_name(self) -> Optional[str]:
        """
        :return: name of user-inputted (or read from file) command name (with
        the usage of 'command_validator', the name must exist
        """
        command_name: str = prompt(
            "Input command: ", completer=self.command_completer, history=self.command_history,
            validator=self.command_validator
        ).lower()
        return command_name

    def ask_command_args(self, command: Union[Command, str]) -> Optional[str]:
        """
        Can be canceled by pressing 'escape' on keyboard

        :param command: either name of command name or Command class
        from which arguments will get pulled
        :return: string of arguments converted to appropriate type
        (simple ones e.g. int, str, bool, ..) of given command,
        empty string if command is of type 'None' or command does not have arguments
        """
        # Convert to appropriate type
        if isinstance(command, str):
            command = self.commands.get(command, None)
        # Checks
        if command is None:
            print(f"Cannot ask for arguments of command type: 'None' !")
            return None
        elif len(command.args.keys()) == 0:  # No arguments to fill
            return ""
        self.argument_validator.set_command(command)
        inputted_args = prompt(
            f"Fill '{command.name}' arguments: ", default=command.get_args_text(),
            history=InMemoryHistory(command.stored_arguments),
            validator=self.argument_validator,
            key_bindings=self.bindings
        )
        return inputted_args

