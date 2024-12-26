from utc.src.constants.file_system.my_file import MyFile
from utc.src.utils.task_manager import TaskManager
from utc.src.constants.static import FilePaths
from utc.src.utils.options.Options import Options
from typing import Set, Dict


class NetConvertOptions(Options):
    """
    Class representing options for netconvert command (program) and generating
    shell command for modifying / converting networks.
    """
    def __init__(self):
        super().__init__("netconvert")
        self.set_output_switch("-o")
        # Template for network conversion ('.osm' -> '.net.xml')
        self.conversion_template: Dict[str, str] = {
            "geometry.remove": "",  # Remove geometry of buildings
            "ramps.guess": "",  # Guess highway ramps, guess roundabouts, join close junctions
            "roundabouts.guess": "",  # Guess roundabouts,
            "junctions.join": "",  # Join close junctions
            "edges.join": "",  # Join close edges
            "remove-edges.isolated": "",  # Remove unconnected edges
            "keep-edges": "1",  # Keep biggest graph of network
        }

    def convert_network(self, in_network_path: str, in_network_type: str = "osm", out_network_path: str = "") -> bool:
        """
        :param in_network_path: path to input network
        :param in_network_type: type of input network (default 'osm')
        :param out_network_path: output network path
        :return: True on success, false otherwise
        """
        # Check file existence
        if not MyFile.file_exists(in_network_path):
            return False
        # Use netconvert command in shell to modify network
        self.options = " ".join(f"{opt} {opt_val}" for opt, opt_val in self.conversion_template.items())
        self.set_input_switch(f"--{in_network_type}")
        return TaskManager.call_shell_block(self.create_command(in_network_path, out_network_path))[0]

    def extract_subgraph(self, from_network: str, edges: Set[str], to_network: str) -> bool:
        """
        Extracts given edges from given network to create new network only containing
        such edges and junctions connecting them.

        :param from_network: name of network file (UTC/utc/data/maps/sumo)
        :param edges: id's of edges to keep in network
        :param to_network: name of new network file, which will get created (UTC/utc/data/maps/sumo)
        :return: True on success, false otherwise
        """
        # Checks
        from_network = FilePaths.MAP_SUMO.format(from_network)
        to_network = FilePaths.MAP_SUMO.format(to_network)
        if not MyFile.file_exists(from_network):
            return False
        elif MyFile.file_exists(to_network, message=False):
            print(f"Output network name: '{to_network}' already exists!")
            return False
        self.options = f" --keep-edges.explicit \"{', '.join(edges)}\""
        self.set_input_switch("-s")
        return TaskManager.call_shell_block(self.create_command(from_network, to_network))[0]


# For testing purposes
if __name__ == "__main__":
    netconvert_options: NetConvertOptions = NetConvertOptions()

