from utc.src.graph.components import Graph, Skeleton
from utc.src.plan_qd.plan_qd_launcher import PlanQDLauncher
from utc.src.constants.file_system import (
    InfoFile, FilePaths, MyFile, SumoConfigFile, SumoNetworkFile,
    MyDirectory, DirPaths, DefaultDir
)
from numpy.random import seed, choice


class AllowedTest:
    """
    """
    def __init__(self):
        self.graph: PlanQDLauncher = PlanQDLauncher()
        self.network_name: str = ""
        seed(42)

    def initialize(self, network_name: str) -> None:
        """
        :param network_name:
        :return: None
        """
        if not MyFile.file_exists(FilePaths.MAP_SUMO.format(network_name)):
            return
        self.network_name = network_name
        self.graph.load_graph_command(network_name)
        self.graph.simplify_command(network_name)

    def create_subgraphs(self, amount: int, c: float) -> None:
        """
        :param amount:
        :param c:
        :return: None
        """
        if amount < 2:
            print(f"Amount must be higher than 2!")
            return
        starting_junctions = list(self.graph.graph.skeleton.starting_junctions)
        ending_junctions = list(self.graph.graph.skeleton.ending_junctions)
        index: int = amount
        while index > 0:
            start: str = choice(starting_junctions)
            end: str = choice(ending_junctions)
            route = self.graph.graph.shortest_path.a_star(start, end)[1]
            if route is None:
                continue
            index -= 1
            self.graph.subgraph_command(f"sg{index}", self.network_name, start, end, c)
        # Merge & save
        merged_name: str = "merged"
        self.graph.merge_command(merged_name, "sg0", "sg1")
        for i in range(2, amount):
            self.graph.merge_command(merged_name, merged_name, f"sg{i}")
        self.graph.save_graph_command(merged_name, merged_name)
        # Save subgraphs
        for i in range(amount):
            self.graph.save_graph_command(f"sg{i}", f"sg{i}")

    def compare_networks(self, amount: int) -> None:
        """
        :return:
        """
        self.graph: PlanQDLauncher = PlanQDLauncher()
        for i in range(amount):
            self.graph.load_graph_command(f"sg{i}")
        self.graph.load_graph_command("merged")
        attributes: dict = self.graph.graphs["merged"].type.get_subgraphs()
        for subgraph in attributes:
            print(subgraph["id"], subgraph["edges"])
            edges: set = set(subgraph["edges"].split(","))
            print(f"Edges length: {len(edges)}")
            print(f"Total edges of graph: {subgraph['id']} -> {len(self.graph.graphs[subgraph['id']].edges)}")
            print(f"Total common edges of graph: {len(edges & self.graph.graphs[subgraph['id']].edges.keys())}")
            if len(edges & self.graph.graphs[subgraph['id']].edges.keys()) != len(edges):
                print(f"ERROR!")
            route_edges: set = set()
            for route in self.graph.graphs[subgraph['id']].routes.values():
                route_edges |= set(route.get_edge_ids())
            print(f"Total route edges: {len(route_edges)}")
            for route_id, route in self.graph.graphs[subgraph["id"]].routes.items():
                if len((set(route.get_edge_ids()) & edges)) != len(route.get_edge_ids()):
                    print(len((set(route.get_edge_ids()) & edges)), len(route.get_edge_ids()))
                    print(f"Error at route: {route_id} -> {set(route.get_edge_ids()) & edges} != {route.get_edge_ids()}")


if __name__ == "__main__":
    temp: AllowedTest = AllowedTest()
    temp.initialize("Sydney")
    # temp.create_subgraphs(5, 1.25)
    temp.compare_networks(5)





