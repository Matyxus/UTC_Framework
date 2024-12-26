from utc.src.constants.static.file_constants import DirPaths, FileExtension
from utc.src.constants.file_system.file_types.xml_file import XmlFile
from utc.src.graph import Graph, RoadNetwork
from typing import Dict, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt


class CongestionVisualizer:
    """
    Class for visualizing heatmaps of Congestion Indexes on given road networks,
    used warm colors for positive values, cold for negative.
    """
    def __init__(self):
        pass

    def plot_ci(self, congestion_array: np.ndarray, graph: Graph, save_path: str = "") -> None:
        """
        :param congestion_array: loaded congestion index data into array
        :param graph: on which to visualize the data
        :param save_path: path to save image at (None by default)
        :return: None
        """
        if not self.check_array(congestion_array, graph):
            return
        fig, ax = graph.display.initialize_plot(
            title=f"Congestion Index of: {graph.road_network.map_name}",
            background_color="white"
        )
        graph.display.render_edges(
            ax, graph.road_network.get_edge_list(),
            colors=plt.get_cmap("Reds")(congestion_array)
        )
        graph.display.show_plot(ax, save_path)
        return

    def plot_ci_diff(
            self, ci_array1: np.ndarray, ci_array2: np.ndarray, graph: Graph,
            save_path: str = "", axes=None) -> None:
        """
        Plots heatmap which visualizes the difference between two congestion array,\n
        diff = ci_array1 - ci_array2, positive values are colored by warm color, negative by cold.

        :param ci_array1: loaded congestion index data into array
        :param ci_array2: loaded congestion index data into array
        :param graph: on which to visualize the data
        :param save_path: path to save image at (None by default)
        :param axes: existing plot axes (by default none)
        :return: None
        """
        if not (self.check_array(ci_array1, graph) and self.check_array(ci_array2, graph)):
            return
        if axes is None:
            fig, ax = graph.display.initialize_plot(
                title=f"Congestion Index of: {graph.road_network.map_name}",
                background_color="white"
            )
        else:
            ax = axes
        congestion_diff: np.ndarray = (ci_array1 - ci_array2)
        # Create arrays to store colors
        colors: np.ndarray = np.zeros(congestion_diff.shape + (4,))  # RGBA colors
        # Apply colormap for values in the range [0, 1]
        colors[congestion_diff >= 0] = plt.cm.Reds(congestion_diff[congestion_diff >= 0])
        # Apply reversed colormap for values in the range [-1, 0]
        colors[congestion_diff < 0] = plt.cm.Blues(-congestion_diff[congestion_diff < 0])
        graph.display.render_edges(
            ax, graph.road_network.get_edge_list(),
            colors=colors, adjust_colors=True
        )
        # graph.display.render_edges(
        #     ax, [graph.road_network.get_edge("-31818#22")],
        #     colors="purple"
        # )
        # print(f"CI of: '-31818#22' is: {congestion_diff[graph.road_network.get_edge('-31818#22').internal_id]}")
        # print(f"Color is: {colors[graph.road_network.get_edge('-31818#22').internal_id] * 255}")
        if axes is None:
            graph.display.show_plot(ax, save_path)
        return

    # ------------------------------------------ Utils ------------------------------------------

    def load_ci(self, edge_data: str, graph: Graph, window: Optional[Tuple[float, float]] = None) -> Optional[np.ndarray]:
        """
        :param edge_data: edge data
        :param graph: on which we want the data to be (i.e. the other edges will be filtered)
        :param window: time window from which we want the data to be (from, to)
        :return: Congestion index values as
        """
        if not XmlFile.file_exists(edge_data, True):
            return
        elif window is None:
            window = (0, float("inf"))
        xml_file: XmlFile = XmlFile(edge_data)
        # Edge_id : CongestionIndex
        ci_map: Dict[str, float] = dict.fromkeys(graph.road_network.edges.keys(), 0.)
        ci_counter: Dict[str, int] = dict.fromkeys(ci_map.keys(), 0)
        n_intervals: int = 0
        for interval in xml_file.root.findall("interval"):
            if float(interval.attrib["begin"]) < window[0]:
                continue
            elif float(interval.attrib["end"]) > window[1]:
                break
            n_intervals += 1
            for edge in interval.findall("edge"):
                if edge.attrib["id"] not in ci_map:
                    continue
                elif "congestionIndex" not in edge.attrib:
                    print(f"Edge: {edge.attrib['id']} is missing attribute 'congestionIndex' !")
                    continue
                ci_map[edge.attrib["id"]] += float(edge.attrib["congestionIndex"])
                ci_counter[edge.attrib["id"]] += 1
        print(f"Loaded CI of: {edge_data}, intervals: {n_intervals}")
        divs: np.ndarray = np.array(list(ci_counter.values()))
        divs[np.where(divs == 0)] = 1
        return np.array(list(ci_map.values())) / divs

    def check_array(self, congestion_array: np.ndarray, graph: Graph) -> bool:
        """
        :return:
        """
        if np.any((congestion_array < 0) | (congestion_array > 1)):
            print("Congestion Indexes must be values in interval <0, 1> !")
            return False
        elif congestion_array.shape[0] != len(graph.road_network.edges):
            print("Number of Congestion Indexes does not equal number of edges !")
            return False
        return True


if __name__ == '__main__':
    visualizer: CongestionVisualizer = CongestionVisualizer()
    network: str = "DCC"
    graph: Graph = Graph(RoadNetwork())
    if not graph.loader.load_map(network):
        raise FileNotFoundError(f"Error unable to locate network: '{network}'")
    data = [
        DirPaths.SCENARIO_STATISTICS.format("itsc_25200_32400_planned") + "/stats_full_edgedata.out.xml",
        DirPaths.SCENARIO_STATISTICS.format("itsc_25200_32400") + "/stats_full_edgedata.out.xml"
    ]
    array1 = visualizer.load_ci(data[0], graph)
    array2 = visualizer.load_ci(data[1], graph)
    visualizer.plot_ci_diff(array1, array2, graph)







