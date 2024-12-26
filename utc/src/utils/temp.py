from utc.src.clustering.gravitational.congestion_visualizer import CongestionVisualizer
from utc.src.constants.static.file_constants import DirPaths, FileExtension
from utc.src.graph import Graph, RoadNetwork
from typing import Dict, Tuple, Optional, List
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec



def generate_figure(original: Graph, regions: List[Graph], edge_data: List[str]) -> None:
    """


    :param original: Original graph
    :param regions: 3 regions of the original graph
    :param edge_data: edge data (original, planned)
    :return: None
    """
    visualizer: CongestionVisualizer = CongestionVisualizer()
    # Create a figure
    fig = plt.figure(figsize=(12, 8))
    plt.tight_layout() # Before regions, since 'annotate' makes the plot smaller
    # Create a GridSpec with 3 rows and 3 columns
    gs = gridspec.GridSpec(2, 3, height_ratios=[3, 1])
    # Top subplot that spans all 3 columns
    ax1 = fig.add_subplot(gs[0, :])  # Full row (row 0, all columns)
    # Bottom subplots
    ax2 = fig.add_subplot(gs[1, 0])  # Bottom left (row 1, column 0)
    ax3 = fig.add_subplot(gs[1, 1])  # Bottom middle (row 1, column 1)
    ax4 = fig.add_subplot(gs[1, 2])  # Bottom right (row 1, column 2)
    # Plot each graph
    for i, (ax, current_graph) in enumerate(zip([ax1, ax2, ax3, ax4], [original] + regions)):
        # Render CI
        planned_array = visualizer.load_ci(edge_data[0], current_graph, (25200, 32400))
        orig_array = visualizer.load_ci(edge_data[1], current_graph, (25200, 32400))
        visualizer.plot_ci_diff(planned_array, orig_array, current_graph, axes=ax)
        ax.autoscale_view(True, True, True)
        ax.set_title(current_graph.road_network.name)
        # Arrows & rectangles for sub regions
        if i != 0:
            coords: np.ndarray = np.array([(junction.x, junction.y) for junction in current_graph.road_network.get_junctions_list()])
            x, y = np.mean(coords, axis=0)
            # width, height = abs(max(coords[:, 0]) - min(coords[:, 0])), abs(max(coords[:, 1]) - min(coords[:, 1]))
            # ax1.add_patch(Rectangle(
            #     (x-(width / 2), y-(height / 2)),  # Bottom-left corner coordinates
            #     width * 0.75,  # Width of the rectangle
            #     height * 0.75,  # Height of the rectangle
            #     linewidth=0.5,  # Border width
            #     edgecolor='grey',  # Border color
            #     alpha=0.3,
            #     facecolor='none'  # Transparent fill
            # ))
            ax1.annotate(
                '',  # No text
                xy=(x, y),  # Target point on the top subplot
                xycoords='data',  # Coordinates are data-based
                xytext=(0.5, 0.5),  # Relative point in the bottom subplot
                textcoords=ax.transAxes,  # Bottom subplot relative coordinates
                arrowprops=dict(arrowstyle="-", color='grey', lw=0.5, alpha=0.5)
            )
    # Plot
    fig.subplots_adjust(top=0.95, bottom=0.05, left=0.05, right=0.95, hspace=0.3, wspace=0.3)
    # plt.tight_layout()
    plt.show()
    return


if __name__ == '__main__':
    network: str = "DCC"
    graph: Graph = Graph(RoadNetwork())
    if not graph.loader.load_map(network):
        raise FileNotFoundError(f"Error unable to locate network: '{network}'")
    graph.road_network.name = "Dublin"
    regions: List[Graph] = [Graph(RoadNetwork()) for _ in range(3)]
    for index, region in enumerate(["DCC_orange", "DCC_green", "DCC_red"]):
        assert(regions[index].loader.load_map(region))
        # regions[index].road_network.name = region[region.index("_")+1:].capitalize()
        regions[index].road_network.name = "Green" if region.endswith("lime") else region[region.index("_")+1:].capitalize()
    data: List[str] = [
        DirPaths.SCENARIO_STATISTICS.format("itsc_25200_32400_planned") + "/stats_full_edgedata.out.xml",
        DirPaths.SCENARIO_STATISTICS.format("itsc_25200_32400") + "/stats_full_edgedata.out.xml"
    ]
    generate_figure(graph, regions, data)



