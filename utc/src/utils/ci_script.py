from utc.src.clustering.gravitational.congestion_visualizer import CongestionVisualizer
from utc.src.constants.static.file_constants import DirPaths, FileExtension
from utc.src.constants.file_system.file_types.xml_file import XmlFile
from utc.src.graph import Graph, RoadNetwork
from utc.src.constants.static.colors import GraphColors
from typing import Dict, Tuple, Optional, List
import numpy as np
from matplotlib.patches import Circle
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from scipy.spatial import ConvexHull
import matplotlib.gridspec as gridspec




def load_ci(edge_data: str, graph: Graph, window: Optional[Tuple[float, float]] = None) -> list:
    """
    :param edge_data: edge data
    :param graph: on which we want the data to be (i.e. the other edges will be filtered)
    :param window: time window from which we want the data to be (from, to)
    :return: Congestion index values as
    """
    if not XmlFile.file_exists(edge_data, True):
        return None
    elif window is None:
        window = (0, float("inf"))
    xml_file: XmlFile = XmlFile(edge_data)
    # Edge_id : CongestionIndex
    ci_map: Dict[str, float] = {edge_id: 0. for edge_id in graph.road_network.edges}
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
    print(f"Loaded CI of: {edge_data}, intervals: {n_intervals}")
    return np.array(list(ci_map.values())) / n_intervals


if __name__ == '__main__':
    network: str = "lust"
    graph: Graph = Graph(RoadNetwork())
    if not graph.loader.load_map(network):
        raise FileNotFoundError(f"Error unable to locate network: '{network}'")
    regions: List[Graph] = [Graph(RoadNetwork()) for _ in range(3)]
    for index, region in enumerate(["lust_red", "lust_lime", "lust_orange"]):
        assert(regions[index].loader.load_map(region))
    data: List[str] = [
        DirPaths.SCENARIO_STATISTICS.format("lust_25200_32400_planned") + "/stats_full_edgedata.out.xml",
        DirPaths.SCENARIO_STATISTICS.format("lust_25200_32400") + "/stats_full_edgedata.out.xml"
    ]
    planned_lust_ci, orig_lust_ci = load_ci(data[0], graph), load_ci(data[1], graph)
    planned_lust_red_ci, orig_lust_red_ci = load_ci(data[0], regions[0]), load_ci(data[1], regions[0])

    for edge in regions[0].road_network.get_edge_list():
        assert(planned_lust_ci[graph.road_network.get_edge(edge.id).internal_id] == planned_lust_red_ci[edge.internal_id])
    for edge in regions[0].road_network.get_edge_list():
        assert(orig_lust_ci[graph.road_network.get_edge(edge.id).internal_id] == orig_lust_red_ci[edge.internal_id])



