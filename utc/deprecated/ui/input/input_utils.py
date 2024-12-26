from utc.deprecated.ui.command import ArgumentValidator
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from typing import Optional


class InputUtils:
    """
    Class holding utility methods for user input (command history, keybind ings ..)
    """

    bindings: KeyBindings = KeyBindings()

    def __init__(self):
        # Classes for prompt_toolkit 'prompt' method
        self.command_history: Optional[InMemoryHistory] = None
        self.command_completer: Optional[WordCompleter] = None
        self.command_validator: Optional[Validator] = None
        self.argument_validator: Optional[ArgumentValidator] = None

    def is_initialized(self) -> bool:
        """
        :return: true if all classes for input utility are initialized, false otherwise
        """
        return ((
            self.command_history and self.command_completer and
            self.command_validator and self.argument_validator) is not None
        )

    @bindings.add('escape')
    def escape_input(event: KeyPressEvent) -> None:
        """
        Cancels the current prompt

        :return: None
        """
        print("\nCaught 'esc' press, abandoning prompt!\n")
        event.app.exit()
