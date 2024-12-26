from typing import Any, Dict


class Options:
    """
    Super class for classes providing options to shell like commands.
    """
    def __init__(self, command_name: str):
        """
        :param command_name: of command (can be path to executable)
        """
        self.command_name: str = command_name
        self.input_switch: str = ""
        self.output_switch: str = ""
        self.options: str = ""

    def process_options(self, options: Dict[str, Any]) -> bool:
        """
        :param options: command options with their arguments
        :return: True on success, false otherwise
        """
        if options is None:
            return False
        for option_name, option_value in options.items():
            # Check if there is argument
            if option_value:
                self.options += f" {option_name} {option_value}"
            else:
                self.options += f" {option_name}"
        return True

    def set_input_switch(self, input_switch: str) -> None:
        """
        :param input_switch: switch to select input file type (e.g. '--osm' when using netconvert)
        :return: None
        """
        self.input_switch = input_switch

    def set_output_switch(self, output_switch: str) -> None:
        """
        :param output_switch: switch to select start processing output (e.g. '-o' when using netconvert)
        :return: None
        """
        self.output_switch = output_switch

    def create_command(self, input_file: str = "", output_file: str = "") -> str:
        """
        :return:
        """
        ret_val: str = self.command_name
        # Add input file
        if input_file:
            ret_val += f" {self.input_switch} {input_file}"
        # Add options to command
        ret_val += " " + self.options
        # Add output file
        if output_file:
            ret_val += f" {self.output_switch} {output_file}"
        return ret_val



