from utc.src.constants.options.options import Options
from utc.src.constants.options.logging_options import LoggingOptions
from utc.src.constants.options.misc_options import InfoOptions
from dataclasses import dataclass, asdict


@dataclass
class PlottingOptions(Options):
    """ Data Class for Gravitational Clustering plotting """
    frequency: int = 0
    heatmap: bool = True
    planets: bool = True
    cluster_size: int = 200

    # Already validated by GravClusteringOptions
    def validate_options(self) -> bool:
        return True


@dataclass
class GravClusteringOptions(Options):
    """ Data Class for Gravitational Clustering algorithm """
    # Main
    data_path: str
    network: str
    multiplier: float = 10.0
    start_time: float = 0
    end_time: float = None
    iterations: int = 100
    merging_radius: float = 10.0
    plotting: PlottingOptions = None
    # Misc
    info: InfoOptions = None
    logs: LoggingOptions = None

    def validate_options(self) -> bool:
        return (
            self.validate_data(asdict(self), "GravClusteringOptions") and
            None not in (self.info, self.logs)
        )


# For testing purposes
if __name__ == '__main__':
    from json import load
    from utc.src.constants.static.file_constants import FilePaths
    file_path: str = FilePaths.CONFIG_FILE.format("clustering_config")
    with open(file_path, "r") as json_file:
        data = load(json_file)
    clustering_options: GravClusteringOptions = Options.dataclass_from_dict(GravClusteringOptions, data)
