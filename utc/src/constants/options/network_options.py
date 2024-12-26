from utc.src.constants.options.options import Options
from dataclasses import dataclass, asdict


@dataclass
class TopkaOptions(Options):
    """ Data class for TopKA* algorithm options """
    c: float = 1.3
    k: int = 3000

    def validate_options(self) -> bool:
        return self.validate_data(asdict(self), "TopkaOptions")


@dataclass
class DbscanOptions(Options):
    """ Data class for DBSCAN algorithm information options """
    eps: float = 0.26
    min_samples: int = 2
    min_routes: int = 10
    metric: str = "shortest_length"
    k: float = 1

    def validate_options(self) -> bool:
        return self.validate_data(asdict(self), "DbscanOptions")


@dataclass
class NetworkOptions(Options):
    """ Data class for road network options (includes simplifying, TopKA*, DBSCAN) """
    simplify: bool = True
    topka: TopkaOptions = None
    dbscan: DbscanOptions = None

    def validate_options(self) -> bool:
        return isinstance(self.simplify, bool) and None not in (self.topka, self.dbscan)


# For testing purposes
if __name__ == '__main__':
    from json import load
    from utc.src.constants.static.file_constants import FilePaths
    file_path: str = FilePaths.CONFIG_FILE.format("pddl_config")
    with open(file_path, "r") as json_file:
        data = load(json_file)
    network_options: NetworkOptions = Options.dataclass_from_dict(NetworkOptions, data["network_options"])


