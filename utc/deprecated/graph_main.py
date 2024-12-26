from typing import Dict, Set
from utc.src.graph.network import RoadNetwork, Graph, Route
from utc.deprecated.ui import UserInterface, Command
from utc.src.constants.static import FilePaths
from utc.src.constants.file_system import MyFile
from utc.src.constants.file_system.directory_types import ScenarioDir
from utc.src.utils.options import NetConvertOptions
from typing import List, Tuple, Optional


class GraphMain(UserInterface):
    """ Class that launches program for graph manipulation, ask user for input """

    def __init__(self, log_commands: bool = True):
        super().__init__("graph", log_commands)
        # Graph modules set to currently used graph
        self.graph: Graph = Graph(RoadNetwork())
        # Maps names of graphs to Graph class
        self.graphs: Dict[str, RoadNetwork] = {}

    def initialize_commands(self) -> None:
        super().initialize_commands()
        self.user_input.add_command([
            Command("load_graph", self.load_graph_command),
            Command("plot_graph", self.plot_graph_command),
            Command("simplify", self.simplify_command),
            Command("subgraph", self.subgraph_command),
            Command("merge", self.merge_command),
            Command("save_graph", self.save_graph_command),
            Command("print_graphs", self.print_graphs_command),
            Command("delete_graph", self.delete_command),
        ])

    # ----------------------------------------- Commands -----------------------------------------

    # ----------- Logging -----------

    @UserInterface.log_command
    def load_graph_command(self, map_name: str) -> None:
        """
        :param map_name: load map from /Maps/sumo/map_name.net.xml and creates graph named map_name
        :return: None
        """
        temp: RoadNetwork = RoadNetwork()
        self.graph.set_skeleton(temp)
        # Error while loading
        if not self.graph.loader.load_map(map_name):
            return
        self.graphs[map_name] = temp

    @UserInterface.log_command
    def simplify_command(self, graph_name: str, plot: bool = False) -> None:
        """
        Replaces junctions forming roundabouts with single junction,
        removes junctions that do not need to be in graph

        :param graph_name: name of graph to simplify
        :param plot: bool (true/false), if process should be displayed
        :return: None
        """
        if not self.graph_exists(graph_name):
            return
        print(f"Junctions before simplify: {len(self.graphs[graph_name].junctions.keys())}")
        self.graph.set_skeleton(self.graphs[graph_name])
        self.graph.simplify.simplify_graph(self.graph.display if plot else None)
        print(f"Junctions after simplify: {len(self.graphs[graph_name].junctions.keys())}")

    @UserInterface.log_command
    def subgraph_command(
            self, subgraph_name: str, graph_name: str, from_junction: str,
            to_junction: str, c: float, plot: bool = False
         ) -> Optional[List[Route]]:
        """
        :param subgraph_name: new name of created sub-graph
        :param graph_name: name of graph from which sub-graph will be made
        :param from_junction: starting junction of sub-graph
        :param to_junction: ending junction of sub-graph
        :param c: maximal route length (shortest_path * c), must be higher than 1
        :param plot: bool (true, false), if process should be displayed
        :return: None
        """
        if not self.graph_exists(graph_name):
            return
        self.graph.set_skeleton(self.graphs[graph_name])
        routes: List[Route] = self.graph.shortest_path.top_k_a_star(
            from_junction, to_junction, c, self.graph.display if plot else None
        )
        # -------------------------------- Init --------------------------------
        sub_graph: RoadNetwork = self.graph.sub_graph.create_sub_graph(routes)
        if sub_graph is None:
            print("Could not create subgraph")
            return None
        sub_graph.set_name(subgraph_name)
        self.graphs[subgraph_name] = sub_graph
        print(f"Finished creating sub-graph: {subgraph_name}")
        return routes

    @UserInterface.log_command
    def merge_command(self, graph_name: str, graph_a: str, graph_b: str, plot: bool = False) -> None:
        """
        :param graph_name: new name of created graph
        :param graph_a: name of first graph (which will be merged)
        :param graph_b: name of second graph (which will be merged)
        :param plot: bool (true, false), if process should be displayed
        :return: None
        """
        # Checks
        if not self.graph_exists(graph_b):
            return
        elif not self.graph_exists(graph_b):
            return
        # Merge
        self.graph.set_skeleton(self.graphs[graph_a])
        new_graph: RoadNetwork = self.graph.sub_graph.merge(self.graphs[graph_b], self.graph.display if plot else None)
        if new_graph is None:
            print("Could not merge graphs")
            return
        new_graph.set_name(graph_name)
        self.graphs[graph_name] = new_graph
        print(f"Finished merging graphs: '{graph_a}' with '{graph_b}', created graph: '{graph_name}'")

    @UserInterface.log_command
    def save_graph_command(self, graph_name: str, file_name: str, scenario_name: str = None) -> bool:
        """
        Saves graph into utc/data/maps/osm or, if given scenario_name
        is valid, utc/data/scenarios/scenario_name/maps/networks

        :param graph_name: to be saved
        :param file_name: name of file containing new road network
        :param scenario_name: name of scenario folder this graph belongs to
        :return: true on success, false otherwise
        """
        if not self.graph_exists(graph_name):
            return False
        # Default maps directory
        network_path: str = FilePaths.MAP_SUMO.format(file_name)
        info_path: str = FilePaths.MAP_INFO.format(file_name)
        # Save network to specific scenario
        if scenario_name is not None:
            scenario_dir: ScenarioDir = ScenarioDir(scenario_name)
            if not scenario_dir.dir_exist(scenario_dir.path):
                return False
            elif not scenario_dir.map_dir.initialize_dir_structure():
                return False
            network_path = FilePaths.SCENARIO_MAP.format(scenario_name, file_name)
            info_path = FilePaths.SCENARIO_MAP_INFO.format(scenario_name, file_name)
        graph: RoadNetwork = self.graphs[graph_name]
        # Create subgraph
        options: NetConvertOptions = NetConvertOptions()
        edges: Set[str] = set()
        for route in graph.routes.values():
            edges |= set(route.get_edge_ids())
        success = options.extract_subgraph(graph.map_name, edges, file_name)
        # File was not created
        if not success or not MyFile.file_exists(network_path):
            return False
        # Save info file if logging is enabled
        if self.logging_enabled:
            self.save_log(info_path, commands=self.reconstruct_graph(graph_name))
        return True

    # ----------- Not logged -----------

    def plot_graph_command(self, graph_name: str) -> None:
        """
        :param graph_name: name of graph to be displayed
        :return: None
        """
        if not self.graph_exists(graph_name):
            return
        self.graph.set_skeleton(self.graphs[graph_name])
        self.graph.display.plot()

    def print_graphs_command(self) -> None:
        """
        Prints names of all created sub-graphs

        :return: None
        """
        print("Printing all graphs names:")
        for index, graph_name in enumerate(self.graphs.keys()):
            print(f"{index+1}\t" + graph_name)

    def delete_command(self, graph_name: str) -> None:
        """
        :param graph_name: name of graph to be deleted
        :return: None
        """
        if not self.graph_exists(graph_name):
            return
        self.graphs.pop(graph_name)

    # ----------------------------------------- Utils -----------------------------------------

    def graph_exists(self, graph_name: str, message: bool = True) -> bool:
        """
        :param graph_name: to be checked for existence
        :param message: if message about graph not existing should be printed (default true)
        :return: true if graph exists, false otherwise
        """
        if graph_name not in self.graphs:
            if message:
                print(f"Graph: '{graph_name}' does not exist!")
            return False
        return True

    def reconstruct_graph(self, graph_name: str) -> Optional[List[Tuple[str, str]]]:
        """
        :param graph_name: name of graph to be reconstructed
        :return: all necessary command names and their arguments,
        about how given graph was constructed
        """
        if not self.logging_enabled:
            print(f"Logging is not enabled, cannot reconstruct graph: {graph_name}")
            return None
        elif not self.commands_log:
            print(f"Command log is empty!")
            return None
        elif not self.commands_log[-1].name == "save_graph":
            print(f"Expected last command to be 'save_graph' !")
            return None
        ret_val: List[Tuple[str, str]] = []
        searching_for: Set[str] = {graph_name}
        index: int = len(self.commands_log)-2
        while len(searching_for) != 0 and index > -1:
            # Extract log
            command_log = self.commands_log[index]
            command_args: Dict[str, str] = command_log.get_args_dict()
            current: Tuple[str, str] = (command_log.name, command_log.get_args_text())
            # Check command name
            if command_log.name == "subgraph" and command_args["subgraph_name"] in searching_for:
                # Return the command and search how "network" was created (from which current graph originated)
                searching_for.remove(command_args["subgraph_name"])
                searching_for.add(command_args["graph_name"])
                ret_val.append(current)
            elif command_log.name == "merge" and command_args["graph_name"] in searching_for:
                searching_for.remove(command_args["graph_name"])
                # Search subgraph\s from which current graph was merged
                searching_for.add(command_args["graph_a"])
                searching_for.add(command_args["graph_b"])
                ret_val.append(current)
            elif command_log.name == "similarity_metric" and command_args["new_subgraph"] in searching_for:
                searching_for.remove(command_args["new_subgraph"])
                # Search original subgraph on which metric was applied on
                searching_for.add(command_args["subgraph"])
                ret_val.append(current)
            elif command_log.name == "load_graph" and command_args["map_name"] in searching_for:
                searching_for.remove(command_args["map_name"])
                ret_val.append(current)  # Graph was loaded, end of search
            index -= 1
        save_log = self.commands_log[-1]  # Add 'save_command'
        return ret_val[::-1] + [(save_log.name, save_log.get_args_text())]


# Program start
if __name__ == "__main__":
    launcher: GraphMain = GraphMain(log_commands=True)
    launcher.run()
