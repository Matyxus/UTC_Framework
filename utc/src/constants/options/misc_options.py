from utc.src.constants.options.options import Options
from dataclasses import dataclass, asdict


@dataclass
class CpuOptions(Options):
    """ Data class for CPU options """
    threads: int = 8
    processes: int = 4

    def validate_options(self) -> bool:
        return self.validate_data(asdict(self), "CpuOptions")


@dataclass
class InfoOptions(Options):
    """ Data class for config information options """
    name: str
    config_type: str
    version: str = "0.0.1"
    save: bool = True

    def validate_options(self) -> bool:
        return self.validate_data(asdict(self), "InfoOptions")
