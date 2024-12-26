from utc.deprecated.ui.command.command import Command
from typing import Set, Dict, Union
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.document import Document
from inspect import Parameter


class ArgumentValidator(Validator):
    def __init__(self):
        super().__init__()
        self.command: Command = None
        self.allowed_bool: Set[str] = {"true", "t", "false", "f"}

    def validate(self, document: Document) -> None:
        # If there are no required arguments and text is empty, return
        if not self.command or not (document.text or len(self.command.args) == 0):
            return
        # Parse inputted arguments, check for errors
        inputted_args: Dict[str, str] = self.parse_input(document)
        if type(inputted_args) == ValidationError:
            raise inputted_args
        # Convert arguments to their correct type, check for error
        converted_args: list = self.convert_args(inputted_args, document)
        if type(converted_args) == ValidationError:
            raise converted_args

    # ----------------------------------------------- Utils -----------------------------------------------

    def convert_args(
            self, inputted_args: Dict[str, str],
            document: Union[Document, str]
            ) -> Union[ValidationError, list]:
        """
        :param inputted_args: inputted args by user in dictionary mapping arg_name to arg_value
        :param document: of command line
        :return: List of arguments in their correct type, or ValidationError in case of error
        """
        if isinstance(document, str):
            document = Document(document)
        ret_val: list = []  # List of arguments in correct type
        # Check type of arguments and required arguments
        for arg_name, arg in self.command.args.items():
            # Missing argument
            if arg_name not in inputted_args:
                # Missing required argument, return ValidationError
                if arg.default != Parameter.empty:
                    return ValidationError(
                        message=f"Missing required argument: '{arg_name}'!",
                        cursor_position=document.cursor_position
                    )
                # Missing argument with default value, append default value
                ret_val.append(arg.default)
            # Unchanged default value
            elif arg.default != Parameter.empty and str(arg.default) == inputted_args[arg_name]:
                ret_val.append(arg.default)
            elif arg.annotation == Parameter.empty:  # Unknown type, append as string
                ret_val.append(inputted_args[arg_name])
            elif arg.annotation == bool:  # Check for bool
                if inputted_args[arg_name] not in self.allowed_bool:
                    return ValidationError(
                        message=f"Argument: '{arg_name}' is expecting bool value to be one of: '{self.allowed_bool}'!",
                        cursor_position=document.cursor_position
                    )
                ret_val.append(inputted_args[arg_name] in {"true", "t"})
            else:  # Check for correct type
                try:
                    ret_val.append(arg.annotation(inputted_args[arg_name]))
                except ValueError as _:
                    return ValidationError(
                        message=f"Argument: '{arg_name}' is not of type: '{arg.annotation}', please change it!",
                        cursor_position=document.cursor_position
                    )
        return ret_val

    def parse_input(self, document: Union[Document, str]) -> Union[ValidationError, Dict[str, str]]:
        """
        :param document: document containing text of command line, mouse position etc..
        :return: Dictionary mapping arg_name to arg_value, Validation error in case of bad form of argument
        """
        if isinstance(document, str):
            document = Document(document)
        ret_val: Dict[str, str] = {arg_name: "" for arg_name in self.command.args.keys()}
        cursor_position: int = 0
        for arg in document.text.split():
            # Check if arg contains '=' and quotes
            if arg.count("=") != 1 or arg.count("\"") != 2:
                return ValidationError(
                    message=f"Expecting arguments: '{arg}' to be in form: arg_name=\"arg_value\", do not change them!",
                    cursor_position=cursor_position
                )
            cursor_position += len(arg) - 1  # Put mouse cursor between quotes
            arg = arg.split("=")  # Separate arg name and value
            arg_name: str = arg[0]
            if arg_name not in ret_val:
                return ValidationError(
                    message=f"Found unknown argument: '{arg_name}'!",
                    cursor_position=cursor_position
                )
            elif arg[1][0] != "\"" or arg[1][-1] != "\"":
                return ValidationError(
                    message=f"Expecting arguments: '{arg}' to be in form: arg_name=\"arg_value\", do not change them!",
                    cursor_position=cursor_position
                )
            arg_value: str = arg[1].replace("\"", "")
            # Check if required argument has some value
            if self.command.args[arg_name].default == Parameter.empty and not arg_value:
                return ValidationError(
                    message=f"Required argument: '{arg_name}' does not have value!",
                    cursor_position=document.cursor_position
                )
            ret_val[arg_name] = arg_value
        return ret_val

    def set_command(self, command: Command) -> None:
        """
        :param command: to be set
        :return: None
        """
        self.command = command
