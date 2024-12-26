from utc.src.graph import Graph, RoadNetwork
from typing import Dict, List, Tuple, Set
from mycolorpy import colorlist as mcp
import numpy as np
from utc.src.analysis.GravClustering import GravClustering


class Analysis:
	"""
	Class performing analysis on edge based data generated from simulation and on clusters made
	by grav clustering.
	"""
	def __init__(self, data_path: str, network_name: str, **kwargs):
		self.grav_clustering: GravClustering = GravClustering(data_path, network_name, **kwargs)
		self.graph: Graph = self.grav_clustering.graph

	# ------------------------------------------ Plots ------------------------------------------

	def borders_network_plot(
			self, colors: List[str], clusters: Dict[int, List[str]],
			save_path: str = "", how_many: int = 5, four_in_one_plot: bool = True
		) -> None:
		"""
		Plot the borders of clusters

		:param colors: colors of the clusters
		:param clusters: made by gravitational clustering
		:param save_path: of plotted figure
		:param how_many: how many border edges to plot/keep
		:param four_in_one_plot: plot all 4 border plots in one 2by2 subplot
		:return: None
		"""
		print(f">>> Plotting borders of clusters {save_path}")

		# Find incoming and outgoing edges of clusters
		clusters_borders_in: Dict[int, List[str]] = {}
		clusters_borders_out: Dict[int, List[str]] = {}
		for leader, members in clusters.items():
			borders = self.get_border_edges_in_out(members)
			clusters_borders_in[leader] = borders[0]
			clusters_borders_out[leader] = borders[1]
		# Initialize plotting
		fig, axes = None, None
		if four_in_one_plot:
			fig, axes = self.graph.display.initialize_plot(rows=2, cols=2)

		self.grav_clustering.clusters_network_plot(
			colors, clusters_borders_in, save_path=f"IN_{save_path}" if save_path != "" else "",
			title="IN_200", ax_in=axes[0, 0] if four_in_one_plot else None
		)
		self.grav_clustering.clusters_network_plot(
			colors, clusters_borders_out, save_path=f"OUT_{save_path}" if save_path != "" else "",
			title="OUT_200", ax_in=axes[0, 1] if four_in_one_plot else None
		)
		# Plot only the most frequent (with traffic) borders
		best_in = self.choose_frequent_borders(clusters_borders_in, how_many)
		best_out = self.choose_frequent_borders(clusters_borders_out, how_many)
		self.grav_clustering.clusters_network_plot(
			colors, best_in, save_path=f"BEST_IN_{save_path}" if save_path != "" else "",
			title=f"BEST-{how_many}_IN_200", ax_in=axes[1, 0] if four_in_one_plot else None
		)
		self.grav_clustering.clusters_network_plot(
			colors, best_out, save_path=f"BEST_OUT_{save_path}" if save_path != "" else "",
			title=f"BEST-{how_many}_OUT_200", ax_in=axes[1, 1] if four_in_one_plot else None
		)
		if four_in_one_plot:
			self.graph.display.show_plot(axes, "Borders_all_in_1.png")

	def final_figure(self) -> None:
		"""
		:return:
		"""
		colors = mcp.gen_color(cmap="hsv", n=10)
		for i in [50, 100, 150, 200]:
			self.grav_clustering.clusters_network_plot(
				colors, self.grav_clustering.choose_clusters(i),
				f"clusters_over_{i}.png"
			)
			self.grav_clustering.clusters_network_plot(
				colors,
				self.combine_touching_clusters(self.grav_clustering.choose_clusters(i)),
				f"COMBINED_clusters_over_{i}.png"
			)

		self.borders_network_plot(
			colors, self.grav_clustering.choose_clusters(200),
			f"borders_over_{200}.png", how_many=10, four_in_one_plot=True
		)

	# ------------------------------------------ Utils ------------------------------------------

	def get_border_edges_in_out(self, members: List[str]) -> Tuple[List[str], List[str]]:
		"""
		:param members: cluster edges
		:return: input and output edges of the cluster border
		"""
		in_edges, out_edges = [], []
		for edge_id in members:
			edge = self.graph.road_network.get_edge(edge_id)

			# get input edges from the border
			from_junction = self.graph.road_network.get_junction(edge.from_junction)
			from_j_in_edges = [e.get_id(False) for e in [r.last_edge() for r in from_junction.get_in_routes()]]
			from_neighbors_outside = [e for e in from_j_in_edges if e not in members]
			if len(from_neighbors_outside) > 0:
				in_edges.append(edge_id)

			# get output edges from the border
			to_junction = self.graph.road_network.get_junction(edge.to_junction)
			to_j_out_edges = [e.get_id(False) for e in [r.last_edge() for r in to_junction.get_out_routes()]]
			to_neighbors_outside = [e for e in to_j_out_edges if e not in members]
			if len(to_neighbors_outside) > 0:
				out_edges.append(edge_id)
		return in_edges, out_edges

	def sort_edges_by_left(self, clusters: Dict[int, List[str]]) -> Dict[int, Dict[str, int]]:
		"""
		:param clusters: made by gravitational clustering
		:return: sorted clusters by 'left' most to least
		"""
		# Matrix of mapping (internal) edge ids to outgoing vehicles
		left_matrix: np.array = np.array(
			list(
				self.grav_clustering.dump_file.sum_attribute(
				self.grav_clustering.intervals, "left", average=True).values()
			), dtype=int
		)[:self.grav_clustering.num_edges]
		sorted_clusters: Dict[int, Dict[str, int]] = {}
		for leader, members in clusters.items():
			left_members: Dict[str, int] = {}
			for member in members:
				left_members[member] = left_matrix[self.graph.road_network.edges[member].get_id()]
			sorted_clusters[leader] = dict(sorted(left_members.items(), key=lambda x: x[1], reverse=True))
		return sorted_clusters

	def choose_frequent_borders(self, clusters: Dict[int, List[str]], count: int) -> Dict[int, List[str]]:
		"""
		:param clusters: made by gravitational clustering
		:param count: the number of most frequent border edges to choose
		"""
		print(f"Choosing '{count}' frequent borders")
		return {k: list(v)[:count] for k, v in self.sort_edges_by_left(clusters).items()}

	def get_border_edges_set(self, members: List[str]) -> List[str]:
		"""
		:param members:
		:return: set of all border edges both in and out
		"""
		x, y = self.get_border_edges_in_out(members)
		return list(set(x+y))

	def combine_touching_clusters(self, clusters: Dict[int, List[str]]) -> Dict[int, List[str]]:
		"""
		:param clusters:
		"""
		# clusters = clusters.copy()
		borders: Dict[int, List[str]] = {}
		possible_combines: Dict[int, Set[int]] = {}  # Dict[leader, Set[other leaders]]
		for leader, members in clusters.items():
			borders[leader] = self.get_border_edges_set(members)
			possible_combines[leader] = set()

		# find which clusters are touching each other
		for leader, members in borders.items():
			# others = [v for k, v in borders.items() if k != leader]
			# others_flat = [element for value_list in others for element in value_list]
			for member in members:
				edge = self.graph.road_network.get_edge(member)
				for other_l, other_ms in borders.items():
					if leader == other_l:
						continue
					neighbors = self.graph.road_network.get_edge_neighbours(edge)

					# find all edges which are touching an edge of a different cluster
					touching_others = [e for e in neighbors if e in other_ms]
					if len(touching_others) > 0:
						possible_combines[leader].add(other_l)
		possible_combines = {k: v for k, v in possible_combines.items() if v != set()}

		# combine the clusters
		while len(possible_combines) > 0:
			# gather all leaders that want to combine
			leader, other_ls = list(possible_combines.items())[0]
			leaders, possible_combines = self.get_leaders(possible_combines, set(), leader)
			leaders: List[int] = list(leaders)

			# find the one with the largest CI
			index_vector: List[int] = [self.grav_clustering.get_index_of(l) for l in leaders]
			new_leader_i: int = np.where(
				self.grav_clustering.congestion_matrix[index_vector] ==
				np.max(self.grav_clustering.congestion_matrix[index_vector])
			)[0][0]
			new_leader: int = leaders[new_leader_i]

			# separate the new leader
			leaders.remove(new_leader)

			# combine the others into the new leader
			# and remove the combined from possible_combines
			for l in leaders:
				clusters[new_leader] += clusters[l]
				del clusters[l]
				if possible_combines.get(l):
					del possible_combines[l]

		return clusters

	def get_leaders(self, possible_combines: Dict[int, Set[int]], leaders: Set[int], curr_l: int
					) -> Tuple[Set[int], Dict[int, List[int]]]:
		"""
		recursively add all touching clusters into the set leaders
		"""
		# add the current leader
		leaders.add(curr_l)
		# add all his neighbors
		if possible_combines.get(curr_l):
			temp = possible_combines[curr_l]
			del possible_combines[curr_l]
			for l in temp:
				leaders, possible_combines = self.get_leaders(possible_combines, leaders, l)

		return leaders, possible_combines


if __name__ == "__main__":
	analyzer: Analysis = Analysis("../../data/scenarios/Base/edgedata.out.xml", "DCC", from_time=8, to_time=9)
	analyzer.grav_clustering.run(iterations=250, plot_every=50)
	analyzer.final_figure()
	# analyzer.grav_clustering()
	# analyzer.reindex_files()
	# print(f"Success: {ret_val}")

