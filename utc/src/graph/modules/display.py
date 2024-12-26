from utc.src.graph.modules.graph_module import GraphModule
from utc.src.constants.static.graph_attributes import NodeAttributes, EdgeAttributes
from utc.src.constants.static.colors import GraphColors
from utc.src.graph.network import RoadNetwork, Edge, Route, Junction
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection, CircleCollection
from matplotlib.colors import is_color_like
from numpy import ndarray
from typing import List, Set, Tuple, Union, Optional


class Display(GraphModule):
    """ Class displaying graph using matplotlib library """

    def __init__(self, road_network: RoadNetwork):
        super().__init__(road_network)

    def initialize_plot(
            self, rows: int = 1, cols: int = 1,
            fig_size: Tuple[int, int] = (12, 8), title: str = "",
            background_color: str = GraphColors.BACKGROUND
        ) -> Tuple[plt.Figure, plt.Axes]:
        """
        :param rows: of subplot
        :param cols: of subplot
        :param fig_size: of plot (tuple x, y)
        :param title: of window
        :param background_color: of plot
        :return: figure and axes (can be multiple)
        :raises: ValueError if rows or cols are less than 1
        """
        # Check arguments
        if rows < 1 or cols < 1:
            raise ValueError(f"Rows: '{rows}' and cols: '{cols}' must be at least 1!")
        fig_size = (fig_size[0] * rows, fig_size[1] * cols)
        fig, ax = plt.subplots(nrows=rows, ncols=cols, figsize=fig_size)
        # Check for multiple subplots
        if rows > 1 or cols > 1:
            for axes in ax.flatten():
                axes.set_facecolor(background_color)
        else:
            ax.set_facecolor(background_color)
        fig.canvas.manager.set_window_title(self.road_network.name if not title else title)
        return fig, ax

    # -------------------------------------------- Plotting --------------------------------------------

    def plot_graph(self, colored: bool = True, annotate: bool = False) -> None:
        """
        Plots the entire graph with default settings

        :param colored: True if fringe junctions should be colored, false otherwise
        :param annotate: True if junctions should display their internal id, False by default
        :return: None
        """
        fig, ax = self.initialize_plot()
        self.render_graph(ax, colored, annotate)
        if colored:
            self.add_label("o", GraphColors.JUNCTION_START_COLOR, "entry")
            self.add_label("o", GraphColors.JUNCTION_END_COLOR, "exit")
            self.add_label("o", GraphColors.JUNCTION_START_END_COLOR, "entry & exit")
            self.make_legend(3)
        self.show_plot(ax)

    # noinspection PyMethodMayBeStatic
    def show_plot(self, ax: plt.Axes, save_path: str = "") -> bool:
        """
        Shows the rendered plot, auto scales view

        :param ax: axes of current plot
        :param save_path: file path in which plot will be saved (optional)
        :return: True on success, false otherwise
        """
        if ax is None or plt.gca() is None:
            print("Cannot show plot, Axes is of type 'None' !")
            return False
        # Assume we received array
        if not isinstance(ax, plt.Axes):
            for axes in ax.flatten():
                axes.autoscale_view(True, True, True)
        else:
            ax.autoscale_view(True, True, True)
        plt.tight_layout()
        # Save figure
        if save_path:
            plt.savefig(save_path)
        plt.show()
        return True

    # -------------------------------------------- Render Objects --------------------------------------------

    def render_graph(self, ax: plt.Axes, colored: bool = True, annotate: bool = False) -> None:
        """
        :param ax: current matplotlib axes
        :param colored: True if fringe junctions should be colored, false otherwise
        :param annotate: True if junctions should display their internal id, False by default (limited to 100)
        :return: None
        """
        if colored:
            self.render_junctions(ax, self.road_network.get_inner_junctions())
            starting_junction: set = self.road_network.starting_junctions
            ending_junctions: set = self.road_network.ending_junctions
            common: set = (starting_junction & ending_junctions)
            starting_junction ^= common
            ending_junctions ^= common
            self.render_junctions(
                ax, self.road_network.get_junctions(starting_junction),
                colors=GraphColors.JUNCTION_START_COLOR, annotate=annotate
            )
            self.render_junctions(
                ax, self.road_network.get_junctions(ending_junctions),
                colors=GraphColors.JUNCTION_END_COLOR, annotate=annotate
            )
            self.render_junctions(
                ax, self.road_network.get_junctions(common),
                colors=GraphColors.JUNCTION_START_END_COLOR, annotate=annotate
            )
        else:
            self.render_junctions(ax, self.road_network.get_junctions_list(), annotate=annotate)
        self.render_edges(ax, list(self.road_network.edges.values()))
        return

    # noinspection PyMethodMayBeStatic
    def render_junctions(
            self, ax: plt.Axes, junctions: List[Junction],
            sizes: Union[List[int], int] = NodeAttributes.NODE_SIZE,
            colors: Union[List[str], str] = GraphColors.JUNCTION_COLOR,
            annotate: bool = False
        ) -> bool:
        """
        :param ax: plot axes
        :param junctions: to be rendered
        :param sizes: of junctions (radius squared)
        :param colors: of junctions, if None default color of each Node is used
        :param annotate: true if junctions id's (internal) should be displayed, false otherwise
        :return: True on success, false otherwise
        """
        # Checks
        if ax is None:
            print("Axes given for rendering junctions are of type 'None' !")
            return False
        elif not junctions:
            print("Nodes to be rendered are empty!")
            return False
        elif isinstance(sizes, list) and len(sizes) != 1 and len(sizes) != len(junctions):
            print(f"Number of sizes: {len(sizes)}, must equal to junctions: {len(junctions)}")
            return False
        elif isinstance(sizes, int):
            if sizes <= 0:
                print(f"Size of junction must be positive value, got: {sizes} !")
                return False
            sizes = [sizes]
        colors = self.check_colors(colors, junctions)
        if colors is None:
            return False
        # Create collection
        ax.add_collection(
            CircleCollection(
                sizes, color=colors,
                offsets=[node.get_position() for node in junctions],
                transOffset=ax.transData
            )
        )
        # Add id's (internal) of junctions to plot
        if annotate:
            if len(junctions) > 100:
                print("Warning, limit of annotations for junctions is 100 for performance !")
                return True
            for node in junctions:
                ax.annotate(
                    node.get_id(), xy=node.get_position(), color='black',
                    fontsize=NodeAttributes.NODE_LABEL_SIZE, weight='normal',
                    horizontalalignment='center', verticalalignment='center'
                )
        return True

    # noinspection PyMethodMayBeStatic
    def render_edges(
            self, ax: plt.Axes, edges: List[Edge],
            colors: Union[ndarray, List[str], str] = GraphColors.EDGE_COLOR,
            line_width: int = EdgeAttributes.LANE_WIDTH,
            lines_style: str = EdgeAttributes.LINES_STYLE,
            adjust_colors: bool = False
        ) -> bool:
        """
        :param ax: plot axes
        :param edges: to be rendered
        :param colors: of edges, if None default color of each Edge is used
        (can be list/array of one color, or the same size of edges)
        :param line_width: of edges (default 1)
        :param lines_style: of edges (default 'solid')
        :param adjust_colors: True if colors should be adjusted to number of links of edges
        :return: True on success, false otherwise
        """
        # Checks
        if ax is None:
            print("Axes given for rendering edges are of type 'None' !")
            return False
        elif not edges:
            print("Edges to be rendered are empty!")
            return False
        colors = self.check_colors(colors, edges)
        if colors is None:
            return False
        # Colors must be extended, since edges have multiple lanes
        elif adjust_colors:
            colors = self.adjust_colors(edges, colors)
        shapes: list = []
        for edge in edges:
            for lane_params in edge.lanes.values():
                shapes.append(lane_params["shape"])
        ax.add_collection(LineCollection(shapes, linewidth=line_width, color=colors, linestyles=lines_style))
        return True

    def render_routes(
            self, ax: plt.Axes, routes: List[Route],
            colors: Union[List[str], str] = GraphColors.EDGE_COLOR,
            line_width: int = EdgeAttributes.LANE_WIDTH,
            lines_style: str = EdgeAttributes.LINES_STYLE
        ) -> bool:
        """
        :param ax: plot axes
        :param routes: to be rendered
        :param colors: of routes, if None default color of each Edge (forming Route) is used
        :param line_width: of routes (default 1)
        :param lines_style: of routes (default 'solid')
        :return: True on success, false otherwise
        """
        route_edges: Set[str] = set()
        for route in routes:
            route_edges |= set(route.get_edge_ids(False))
        return self.render_edges(ax, self.road_network.get_edges(route_edges), colors, line_width, lines_style)

    # ------------------------------------------ Utils ------------------------------------------

    # noinspection PyMethodMayBeStatic
    def add_label(self, marker: str, color: str, label: str) -> None:
        """
        Adds label to be displayed on legend, uses matplotlib scatter

        :param marker: to be shown
        :param color: of marker
        :param label: text
        :return: None
        """
        plt.scatter([], [], marker=marker, color=color, label=label)

    # noinspection PyMethodMayBeStatic
    def make_legend(self, columns: int) -> None:
        """
        Creates legend on top of a plot

        :param columns: number of items that will be added to legend
        :return: None
        """
        plt.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, 1.08),  # on top, (bottom: (0.5, -0.05))
            fancybox=True, shadow=True,
            ncol=columns
        )

    # noinspection PyMethodMayBeStatic
    def check_colors(
            self, colors: Union[ndarray, List[str], str],
            parts: List[Union[Edge, Junction]],
        ) -> Optional[Union[ndarray, List[str], str]]:
        """
        :param colors: colors to be checked (numpy array or list)
        :param parts: to be rendered (edges or junctions)
        :return: True if colors are correct, false otherwise
        """
        # Check single color
        if isinstance(colors, str):
            if not colors:  # Empty colors, return default color
                return GraphColors.EDGE_COLOR if isinstance(parts[0], Edge) else GraphColors.JUNCTION_COLOR
            elif not is_color_like(colors):
                return None
        else:  # Check single color in list
            if len(colors) == 1 and not is_color_like(colors[0]):
                print(f"Color: {colors} is not valid !")
                return None
            elif len(colors) != 1 and not is_color_like(colors) and len(colors) < len(parts):
                print(f"Number of colors: {len(colors)}, must equal to parts: {len(parts)}")
                return None
        return colors

    # noinspection PyMethodMayBeStatic
    def adjust_colors(self, edges: List[Edge], colors: Union[ndarray, List[str], str]) -> Union[ndarray, list, str]:
        """
        :param edges: edges to be colored
        :param colors: colors (must be same length as edges)
        :return: Adjust list of colors
        """
        if not (isinstance(colors, (ndarray, list)) or len(colors) == len(edges)):
            print("Error, cannot adjust colors, expected colors to be list the same length as edges!")
            return colors
        new_colors = []
        for i, edge in enumerate(edges):
            for _ in range(edge.get_lane_count()):
                new_colors.append(colors[i])
        return new_colors
