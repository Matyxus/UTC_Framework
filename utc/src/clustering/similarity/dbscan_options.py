from utc.src.constants.options.options import Options
from dataclasses import dataclass, asdict


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


# For testing purposes
if __name__ == '__main__':
    from json import load
    from utc.src.constants.static.file_constants import FilePaths
    file_path: str = FilePaths.CONFIG_FILE.format("pddl_config")
    with open(file_path, "r") as json_file:
        data = load(json_file)
    clustering_options: DbscanOptions = Options.dataclass_from_dict(DbscanOptions, data["network"]["dbscan"])
