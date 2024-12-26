from utc.deprecated.ui.command.command_parser import CommandParser
from typing import List, Any, Dict, Optional
from inspect import Parameter, signature, getdoc


class Command:
    """
    Class representing command for UserInput
    """
    def __init__(self, command_name: str, method: callable):
        """
        :param command_name: name of method (used for input)
        :param method: function representing this class (default none)
        """
        self.name: str = command_name
        self.args: Dict[str, Parameter] = CommandParser.get_mapping(method)
        self.method: callable = method
        # Number of arguments, which values must be filled by user (or in file)
        self.required_args: int = sum(1 for arg in self.args.values() if arg.default == Parameter.empty)
        # History of filled arguments for this command
        self.stored_arguments: List[str] = []

    def exec(self, args: List[Any], args_text: str = "") -> Any:
        """
        :param args: list of arguments given to method (any amount / type, their order must be correct)
        :param args_text: text of inputted arguments to be stored (default empty)
        :return: value returned by executed method
        """
        if args_text:
            self.stored_arguments.append(args_text)
        print(f"Executing command: '{self.name}', with arguments: '{args_text}'")
        return self.method(*args)

    # --------------------------------------------- Utils ---------------------------------------------

    def help(self) -> str:
        """
        :return: Command name and arguments of given function, with
        documentation of function assigned to this class
        """
        if self.method is None:
            return f"Missing method for command: '{self.name}', cannot show documentation!"
        ret_val: str = f"Description of command '{self.name}':'{signature(self.method)}'\n"
        documentation: Optional[str] = getdoc(self.method)
        if documentation:  # Check for None and empty string
            ret_val += ("\t" + documentation.replace("\n", "\n\t") + "\n")
        else:  # Handle missing documentation
            ret_val += f"\t No documentation\n"
        return ret_val

    def get_args_text(self) -> str:
        """
        :return: string representation of command arguments (e.g. number="" period="" ...),
        separated by exactly 1 white space
        """
        ret_val: str = " ".join(
            f"{arg_name}=" + (f"\"{arg.default}\"" if arg.default != Parameter.empty else "\"\"")
            for arg_name, arg in self.args.items()
        )
        return ret_val

