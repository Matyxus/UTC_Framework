from utc.src.constants.options.options import Options
from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class LoggingOptions(Options):
    """ Data class for logging options """
    level: str = "DEBUG"
    file: str = "default"
    colored: bool = True
    stream: str = None

    def validate_options(self) -> bool:
        return self.validate_data(asdict(self), "LoggingOptions")

