from utc.deprecated.ui import UserInterface
from utc.src.converter import Converter
from utc.src.pddl import UtcLauncher
from utc.src.graph import GraphMain
from utc.src.simulator import ScenarioMain
from typing import Dict


class Main(UserInterface):
    """
    Main UserInterface subclass, uses other subclasses of UserInterface
    to this one, in order to make access to all commands inside one class
    """
    def __init__(self):
        super().__init__("main")
        # Initialize classes
        self.ui_classes: Dict[str, UserInterface] = {
            "converter": Converter(),
            "graph": GraphMain(),
            "pddl": UtcLauncher(),
            "scenario": ScenarioMain()
        }

    def initialize_input(self) -> None:
        """
        Initializes commands from other subclasses of
        UserInterface to work for this class

        :return: None
        """
        # Merge other UserInterfaces to this one
        super().initialize_input()
        for ui in self.ui_classes.values():
            self.merge(ui)


if __name__ == "__main__":
    main: Main = Main()
    main.run()
