from utc.deprecated.ui.input import UserInput, FileInput, MyInput
from utc.deprecated.ui.command import Command, CommandLogger
from typing import Dict, Any, Optional


class UserInterface(CommandLogger):
    """ Parent class for static/dynamic input, subclass of CommandLogger """

    def __init__(self, class_name: str, log_commands: bool = False):
        super().__init__(log_commands)
        print(f"Launching UserInterface for '{class_name}', initializing objects..")
        self.running = False  # Control of main loop
        self.name = class_name  # Name of subclass
        self.current_ret_val: Any = None
        self.user_input: Optional[MyInput] = None

    # ----------------------------------------- Input -----------------------------------------

    def run(self) -> None:
        """
        Handles input passed from user using prompt_toolkit to ask for
        command name, then (if there are any) asks for arguments of
        chosen command name.
        The same way is handled input passed from redirected file,
        expecting format each line to be: command_name arg1="value" arg2="value2", ...,
        there must be exactly 1 blank space between command names and its parameters

        :return: None
        """
        # Initialize
        print("Starting program, for help type: 'help'")
        print(
            "Input command arguments between \"quotes\"\n"
            "separated by space (arguments with values are optional)."
        )
        self.initialize_input()
        # Main loop
        self.running = True
        while self.running:
            command_name, command_args = self.user_input.get_input()
            self.process_input(command_name, command_args)
        print("Exiting ...")

    def process_input(self, command_name: str, command_args: str) -> bool:
        """
        :param command_name: name of command
        :param command_args: arguments of command
        :return: True on success (command execution is not checked),
        false otherwise
        """
        print(f"Processing input: {command_name}, {command_args}")
        if self.user_input is None or not self.user_input.is_initialized():
            print(f"Cannot process input, call 'initialize_input' first !")
            return False
        elif not self.user_input.command_exists(command_name):
            return False
        elif command_args is None:
            return False
        converted_args: list = self.user_input.convert_args(command_name, command_args)
        if converted_args is None:
            return False
        # Execute
        self.current_ret_val = self.user_input.commands[command_name].exec(converted_args, command_args)
        return True

    def initialize_input(self) -> None:
        """
        Initializes Input class (either FileInput if input
        is redirected from file, otherwise UserInput),
        calls "initialize_commands"

        :return: None
        """
        # Already initialized
        if self.user_input is not None and self.user_input.is_initialized():
            return
        # Initialize UserInput
        if not MyInput.is_redirected():
            self.user_input = UserInput()
        else:
            self.user_input = FileInput()
        self.user_input.initialize_input()
        self.initialize_commands()

    # ----------------------------------------- Commands -----------------------------------------

    def initialize_commands(self) -> None:
        """
        Method for adding initial commands to UserInput, gets called
        after initialize_input, should be overridden by subclasses of
        UserInterface

        :return: None
        """
        if self.user_input is None or not self.user_input.is_initialized():
            print(f"Cannot add commands to UserInput, is not initialized!")
            return
        # Add commands
        self.user_input.add_command([
            Command("help", self.help_command),
            Command("exit", self.exit_command)
        ])

    def help_command(self, command_name: str = "all") -> None:
        """
        :param command_name: name of command to be printed (default all)
        :return: None
        """
        if self.user_input is None:
            print(f"User input is not initialized, use method 'run' !")
            return
        to_print: Dict[str, Command] = {}
        # Print help description of specific command
        if command_name != "all":
            if self.user_input.command_exists(command_name):
                to_print[command_name] = self.user_input.commands[command_name]
            else:  # Unknown command
                print(f"Command: '{command_name}' does not exist, for list of commands type 'help'!")
                return
        else:  # All commands
            to_print = self.user_input.commands
        # Print help description of command\s
        for function_name, command in to_print.items():
            print(command.help())

    def exit_command(self) -> None:
        """
        Quits the program

        :return: None
        """
        self.running = False

    # ----------------------------------------- Utils -----------------------------------------

    def merge(self, other: 'UserInterface') -> None:
        """
        Merges other UserInterface subclasses to current one,
        taking their UserInput class and logging list and changing it for this one

        :param other: different UserInterface subclass
        :return: None
        """
        # Checks
        if not isinstance(other, UserInterface):
            print(f"Unable to merge UserInterface with different type then UserInterface, got: {type(other)} !")
            return
        elif self.user_input is None or not self.user_input.is_initialized():
            print(f"Cannot merge with other UserInterface, UserInput is not initialized!")
            return
        # Change pointer and add commands
        other.commands_log = self.commands_log
        other.user_input = self.user_input
        other.initialize_commands()
