from utc.deprecated.ui.command.command_parser import CommandParser
from utc.src.constants.file_system import InfoFile
from functools import wraps
from typing import List, Dict, Tuple, Set, Optional, Union, Any, Callable


class CommandLogger:
    """
    Class responsible for logging commands and their arguments
    """
    def __init__(self, log_commands: bool = False):
        self.logging_enabled: bool = log_commands
        # List of commands log (in order they were recorded)
        self.commands_log: List[CommandLogger.CommandLog] = []

    class CommandLog:
        """
        Class representing single log of command call, provides utility methods
        """
        def __init__(self, name: str, args: Union[str, Dict[str, Any]]):
            """
            :param name:
            :param args:
            """
            self.name: str = name
            self.args: Union[str, Dict[str, Any]] = args

        def get_args_text(self) -> str:
            """
            :return: arguments format (arg1="value1" arg2="value2", ..)
            """
            if isinstance(self.args, str):
                return self.args
            return " ".join(f'{arg_name}="{arg_value}"' for arg_name, arg_value in self.args.items())

        def get_args_dict(self) -> Optional[Dict[str, Any]]:
            """
            :return: mapping of argument name to its value
            """
            if isinstance(self.args, dict):
                return self.args
            return CommandParser.parse_args_text(self.args)

    def add_logg(self, command_name: str, command_args: Union[str, Dict[str, Any]], message: bool = True) -> None:
        """
        :param command_name: name of command
        :param command_args: arguments of command (either in string format or mapping)
        :param message: if message about logging should be printed
        :return: None
        """
        if not self.logging_enabled:
            print(f"Logging is not enabled, cannot log: '{command_name}' -> '{command_args}' !")
            return
        if message:
            print(f"LOGGING: '{command_name}' -> '{command_args}'")
        self.commands_log.append(CommandLogger.CommandLog(command_name, command_args))

    def save_log(self, file_path: str, commands: List[Tuple[str, str]] = None) -> bool:
        """
        Creates ".info" file at given file_path containing
        ordered commands and their arguments

        :param file_path: in which InfoFile will be created
        :param commands: list of (command name, command args as text) which is to be saved,
        if None, whole command log is used
        :return: true on success, false otherwise
        """
        if not self.logging_enabled:
            print(f"Cannot save logged commands, into: '{file_path}', logging is not enabled!")
            return False
        elif commands is None:
            commands = self.get_commands_pairs()
        return InfoFile("").save(file_path=file_path, commands=commands)

    # ------------------------------------------ Wrappers ------------------------------------------

    def log_command(function: Callable, logger: 'CommandLogger' = None) -> Any:
        """
        Decorator for function to log their command names and arguments in CommandLogger,
        methods should be called [method_name]_command,
        can be used as decorator only by subclasses of logger

        :param function: method being called
        :param logger: class to which the logs will be writen to, default None,
        (only added if method to be logged is not present in subclass of UserInterface)
        :return: return value of function
        """
        @wraps(function)
        def wrapper(*args, **kwargs):
            self: Optional[CommandLogger] = None
            if logger is not None:
                self = logger
            # If logging is done by subclass of CommandLogger the class is first argument
            elif len(args) > 0 and isinstance(args[0], CommandLogger):
                self = args[0]
            # Check if decorator was used on correct class method
            # or given logger is not None and logging is enabled
            if self is not None and self.logging_enabled:
                mapping = CommandParser.get_mapping(function)
                formatted_args: str = CommandParser.get_formatted_args(mapping, keep_default=False)
                arguments: list = list(args[1:]) if isinstance(args[0], CommandLogger) else list(args)
                # Find missing key word arguments
                for arg_name in CommandParser.get_default_args(mapping):
                    if arg_name in kwargs:
                        arguments.append(kwargs[arg_name])
                    else:
                        arguments.append(mapping[arg_name].default)
                command_name: str = str(function.__name__).replace("_command", "")
                # print(formatted_args, arguments)
                # print(args, kwargs)
                self.add_logg(command_name, formatted_args.format(*arguments))
            else:
                print(f"Cannot log method: '{function.__name__}' into logger of type: 'None'!")
            return function(*args, **kwargs)
        # This line is done so that PyCharm shows hints
        # on arguments methods not on decorator
        wrapper: function
        return wrapper

    def set_logger(self, target: object, methods: List[Callable]) -> None:
        """
        Sets self as logging class to given methods of given class

        :param target: class to be logged
        :param methods: methods of given object to be logged
        :return: None
        """
        target_methods: Set[str] = set(dir(target))
        for method in methods:
            if method.__name__ not in target_methods:
                print(f"Unable to log method: '{method}', target: '{type(target)}' does not have it!")
            else:  # Set wrapper
                print(f"Found method: {method.__name__}, setting logger")
                setattr(target, method.__name__, CommandLogger.log_command(method, self))
                print(f"Done setting logger")

    # ------------------------------------------ Utils ------------------------------------------

    def get_command_log(self, command_name: str) -> List['CommandLogger.CommandLog']:
        """
        :param command_name: to be found
        :return: list of CommandLog classes, empty if found none
        """
        return [command_log for command_log in self.commands_log if command_log.name == command_name]

    def add_comment(self, comment: str) -> None:
        """
        :param comment: adds comment to file, name of command is set to ";Comment"
        :return: None
        """
        self.add_logg(";Comment", comment)

    def clear_log(self) -> None:
        """
        Clears all entries of saved commands and their arguments

        :return: None
        """
        self.commands_log.clear()

    def get_commands_pairs(self) -> List[Tuple[str, str]]:
        """
        :return: list of tuples (command name, arguments),
        sorted by their recorded time (order of use)
        """
        return [(command_log.name, command_log.get_args_text()) for command_log in self.commands_log]
