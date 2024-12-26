from typing import List, Dict, Set, Optional
from inspect import Parameter, signature


class CommandParser:
    """
    Class providing static methods to parse functions (e.g. get all
    arguments of function etc..)
    """

    @staticmethod
    def get_formatted_args(args: Dict[str, Parameter], keep_default: bool = True) -> str:
        """

        :param args: dictionary mapping argument name to Parameter Class
        :param keep_default: if default values should be kept in formatted string
        :return: arguments in form: arg_name1="{0}" arg_name2="{1}" ...
        """
        # Empty arguments
        if not len(args.keys()):
            return ""
        ret_val: str = " ".join(
            f"{arg_name}=" + (
                f"\"{arg.default}\"" if (arg.default != Parameter.empty and keep_default)
                else "\"{" + f"{i}" + "}\""
            )
            for i, (arg_name, arg) in enumerate(args.items())
        )
        return ret_val.rstrip()

    @staticmethod
    def get_mapping(method: callable, ignored: Set[Parameter] = None) -> Dict[str, Parameter]:
        """
        :param method: from which mapping will be created
        :param ignored: types of parameters to ignore (by default it is '*args' and '**kwargs'
        :return: Mapping of method parameter name to Parameter clas
        """
        if ignored is None:
            # Remove '*args' and '**kwargs' from function parameters
            ignored = {Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL}
        args: Dict[str, Parameter] = {
            key: value for key, value in signature(method).parameters.items()
            if value.kind not in ignored
        }
        # Remove class method parameter 'self'
        if "self" in args:
            args.pop("self")
        return args

    @staticmethod
    def parse_args_text(args: str) -> Optional[Dict[str, str]]:
        """
        :param args: in input format (arg1="value1" arg2="value2", ..)
        :return: mapping of argument name to value
        """
        if not (args.count("\"") & 1) == 0:
            print(f"Expected number of \" to be even, got: {args}")
            return None
        args = args.replace("\"", "")
        args = args.split()
        if not args:
            print(f"Error in args format: {args}")
            return None
        ret_val: Dict[str, str] = {}
        for arg in args:
            if arg.count("=") != 1:
                print(f"Expected '=' between argument name and value, got: {arg}")
                continue
            arg = arg.split("=")
            if len(arg) != 2:
                print(f"Invalid argument name, value pair: {arg}")
                continue
            ret_val[arg[0]] = arg[1]
        return ret_val

    @staticmethod
    def get_default_args(args: Dict[str, Parameter]) -> List[str]:
        """
        :param args:
        :return: Names of arguments which have default value
        """
        return [arg_name for arg_name in args if args[arg_name].default != Parameter.empty]
