from utc.src.constants.dynamic.arguments import get_args
from utc.src.constants.file_system.file_types.json_file import JsonFile
from utc.src.constants.file_system.file_types.xml_file import XmlFile
from utc.src.clustering.gravitational.grav_clustering_options import GravClusteringOptions
from utc.src.graph import Graph, RoadNetwork
from typing import Dict, List, Union
import numpy as np
import matplotlib.pyplot as plt


class GravClustering:
	"""
	Class clustering areas of high traffic intensity (congestion index) into sub-graphs,
	defining "problematic" regions of road network.
	https://sumo.dlr.de/docs/Simulation/Output/Lane-_or_Edge-based_Traffic_Measures.html
	"""
	def __init__(self, options: GravClusteringOptions):
		"""
		:param options: of gravitational clustering, must be initialized !
		"""
		print("Initializing gravitational clustering ....")
		assert(options is not None)
		self.options: GravClusteringOptions = options
		self.graph: Graph = Graph(RoadNetwork(self.options.network))
		# File checks
		if not self.graph.loader.load_map(self.options.network):
			raise FileNotFoundError(f"Network: '{self.options.network}' does not exist!")
		elif not XmlFile.file_exists(self.options.data_path, False):
			raise FileNotFoundError(f"Data: '{self.options.data_path}' does not exist!")
		# Parameters for grav. clustering
		self.position_matrix: np.array = None
		self.congestion_matrix: np.array = None
		self.index_vectors: np.array = None
		self.clusters: Dict[int, List[int]] = {}  # edge_id : [edge_id, ...]
		self.color_map = plt.get_cmap("hsv")([0.1 * i for i in range(11)])
		self.initialize(self.options.start_time, self.options.end_time)

	def initialize(self, start_time: float = 0, end_time: float = None) -> None:
		"""
		:param start_time: starting time of interval
		:param end_time: ending time of interval
		:return: None
		"""
		np.set_printoptions(suppress=True)
		# Clusters each corresponding to its own edge (mapped to list of edges forming cluster)
		self.clusters = {
			edge.get_id(True): [edge.get_id(True)] for edge in self.graph.road_network.get_edge_list()
		}
		# Initial position of edges (their centroids)
		self.position_matrix: np.array = np.matrix.round(self.create_centroid_matrix(), decimals=3)  # Nx2
		self.congestion_matrix: np.array = np.matrix.round(self.create_ci_matrix(start_time, end_time), decimals=3)
		self.index_vectors: np.array = np.array(list(self.clusters.keys()))
		assert(np.all(self.index_vectors[:-1] <= self.index_vectors[1:]))
		print("Finished initializing all variables")

	# ------------------------------------------ Clustering ------------------------------------------

	def run(self, iterations: int = 200, plot_freq: int = 10, merging_radius: float = 15.0) -> None:
		"""
		:param iterations: number of total iteration to be done
		:param plot_freq: how often should be plot displayed, default every 50 iterations
		:param merging_radius: minimal distance between clusters centers to merge them, default 15 (meters)
		:return: None
		"""
		if not np.all(self.congestion_matrix >= 0):
			print(f"Expected all values of congestion indexes to be above 0 !")
			return
		# Square merging radius
		merging_radius = np.square(merging_radius)
		# Pick some colors for clusters
		if plot_freq > 0:
			if self.options.plotting.heatmap:
				self.ci_network_plot()
			if self.options.plotting.planets:
				self.plot_planets(title="Iteration 0")
		else:  # Increase the value so that plotting does not happen
			plot_freq = iterations + 1
		# ------------ Main loop ------------
		for iteration in range(1, iterations+1):
			print(f"\n### Iteration: {iteration}/{iterations} ###")
			print(f"Clusters({len(self.clusters)})")
			self.step(merging_radius)
			# ------------------ Plot ------------------
			if iteration % plot_freq == 0:
				if self.options.plotting.planets:
					self.plot_planets(title=f"Iteration {iteration}")
				self.clusters_network_plot(self.color_map, self.choose_clusters(self.options.plotting.cluster_size))
			# ------------------ Sub-graphs from clusters ------------------
			if len(self.clusters) == 1:  # Stopping condition
				print("Finished merging all clusters!")
				break
		return

	def step(self, merging_radius: float) -> None:
		"""
		Performs one step of gravitational clustering algorithm.

		:param merging_radius: minimal distance between clusters centers to merge them (squared radius)
		:return: None
		"""
		# ------------------ Calculate movement of edges based on grav. attraction ------------------
		movements: np.array = np.zeros((self.position_matrix.shape[0], 2), dtype=np.float32)
		for i in range(self.position_matrix.shape[0]):
			# Squared distances, gravity requires distance to be squared
			distances: np.array = np.sum(np.square(self.position_matrix - [self.position_matrix[i]]), axis=1)
			distances[i] = 1
			assert(0 not in distances)
			attraction: np.array = self.congestion_matrix / distances
			movements[i] = np.matrix.round(np.dot((self.position_matrix - self.position_matrix[i]).T, attraction), 5)
		self.position_matrix += movements
		# ------------------ Clustering ------------------
		index = 0
		while index < self.position_matrix.shape[0]:
			# Check if edge is still not in cluster
			assert (self.index_vectors[index] in self.clusters)
			# Find edges in merging radius relative to current edge (squared distance, assuming radius squared)
			distances: np.array = np.sum(np.square(self.position_matrix - [self.position_matrix[index]]), axis=1)
			distances[index] = float("inf")  # Avoid merging the same edge
			points: np.array = np.where(distances < merging_radius)[0]
			if len(points) != 0:
				# Get the max CI of edges which are merging
				leader_i = np.argmax(self.congestion_matrix[points])
				leader_index = points[leader_i]
				# New leader index was inside points, replace it with current point
				if self.congestion_matrix[leader_index] > self.congestion_matrix[index]:
					points[leader_i] = index
					index -= 1  # Shift back index, since it wil get removed
				else:
					leader_index = index
				# Move cluster to center of merged clusters
				self.position_matrix[leader_index] = np.mean(
					self.position_matrix[np.append(points, leader_index)], axis=0
				)
				# Add edges to cluster (to current edge - cluster leader)
				for point in points:
					self.clusters[self.index_vectors[leader_index]] += self.clusters.pop(self.index_vectors[point])
					self.congestion_matrix[leader_index] += self.congestion_matrix[point]
				# Remove edges from further calculation
				self.index_vectors = np.delete(self.index_vectors, points)
				self.congestion_matrix = np.delete(self.congestion_matrix, points)
				self.position_matrix = np.delete(self.position_matrix, points, axis=0)
			index += 1
		return

	# ------------------------------------------ Plots ------------------------------------------

	def clusters_network_plot(
			self, colors: Union[np.ndarray, List[str]], clusters: Dict[int, List[int]],
			save_path: str = "", title: str = "", ax_in: plt.Axes = None
		) -> None:
		"""
		Plot the road network

		:param colors: colors of the clusters
		:param clusters: clusters made by the algorithm
		:param save_path: location to save image in
		:param title: title of the plot
		:param ax_in: axes of the plot (can be existing plot)
		:return: None
		"""
		if len(clusters) == 0:
			return
		# print(f"Plotting {len(clusters)} clusters")
		# Pick current axis
		if ax_in is None:
			fig, ax = self.graph.display.initialize_plot(background_color="white", title=title)
		else:
			ax = ax_in
		# Plot all edges
		self.graph.display.render_edges(ax, self.graph.road_network.get_edge_list())
		# Plot colored edges
		clusters_size: int = len(clusters)
		for index, cluster in enumerate(clusters.values()):
			self.graph.display.render_edges(ax, self.graph.road_network.get_edges(cluster), colors[index % clusters_size])
		# Display immediately
		if ax_in is None:
			self.graph.display.show_plot(ax, save_path)
		return

	def ci_network_plot(self, save_path: str = "", temperature: bool = False) -> None:
		"""
		Plot the road network and congestion index as the colormap

		:param temperature: True if congestion index is taken as difference of heatmaps (values from -1 to 1)
		:param save_path: path to save image at
		:return: None
		"""
		# print(f"Plotting Congestion Index heatmap, network: '{self.graph.road_network.map_name}'")
		fig, ax = self.graph.display.initialize_plot(
			title=f"Congestion Index of: {self.graph.road_network.map_name}",
			background_color="white"
		)
		# print(f"Congestion matrix shape: {self.congestion_matrix.shape}")

		def get_colors() -> np.ndarray:
			"""
			:return: numpy array of colors, Reds if temperature is not chosen
			"""
			if not temperature:
				return plt.get_cmap("Reds")(self.congestion_matrix / 10)
			# Create arrays to store colors
			colors: np.ndarray = np.zeros(self.congestion_matrix.shape + (4,))  # RGBA colors
			# Apply colormap for values in the range [0, 1]
			colors[self.congestion_matrix >= 0] = plt.cm.Reds(self.congestion_matrix[self.congestion_matrix >= 0] / 10)
			# Apply reversed colormap for values in the range [-1, 0]
			colors[self.congestion_matrix < 0] = plt.cm.Blues(-(self.congestion_matrix[self.congestion_matrix < 0] / 10))
			return colors

		self.graph.display.render_edges(
			ax, self.graph.road_network.get_edge_list(),
			colors=get_colors()
		)
		self.graph.display.show_plot(ax, save_path)

	def plot_planets(self, title: str = "", save_path: str = "") -> None:
		"""
		Plots clusters as planets, each point is represented as circle,
		its size depend on its weight which increases during merging

		:param title: title of the plot
		:param save_path: path to save image at (default None)
		:return: None
		"""
		# print("Plotting planets")
		fig, ax = self.graph.display.initialize_plot(background_color="white")
		ax.scatter(self.position_matrix[:, 0], self.position_matrix[:, 1], s=self.congestion_matrix)
		ax.set_title(title)
		self.graph.display.show_plot(ax, save_path)

	# ------------------------------------------ Utils ------------------------------------------

	def create_centroid_matrix(self) -> np.array:
		"""
		:return: matrix of centroid points of all network edges
		"""
		centroid_matrix: np.array = np.zeros(shape=(len(self.graph.road_network.edges), 2), dtype=np.float32)
		for edge in self.graph.road_network.edges.values():
			# Values must be taken from lanes, since edges can have the same shape!
			centroid_matrix[edge.get_id(True)] = np.array(edge.get_centroid())
		# Check if there are lanes which have the same position (can happen -> ITSC scenario), shift them
		unique_elements, counts = np.unique(centroid_matrix, axis=0, return_counts=True)
		duplicates = unique_elements[counts > 1]
		if len(duplicates) != 0:
			print(f"Warning, detected {len(duplicates)} Edge's, which lanes share the same coordinates, shifting!")
			# Shift duplicate coordinates
			for duplicate in duplicates:
				# Find the indexes of duplicates
				duplicate_indexes = np.unique(np.where(centroid_matrix == duplicate)[0])
				# Change to python integers
				edge_ids: List[str] = [self.graph.road_network.get_edge(int(i)).get_id() for i in duplicate_indexes]
				print(f"Edges sharing same coordinates: {edge_ids}")
				# Shift each duplicate by: 0.1 * duplicate_number
				for i in range(1, len(duplicate_indexes)):
					centroid_matrix[duplicate_indexes[i]] += (0.1 * i)
		return centroid_matrix

	def create_ci_matrix(self, from_time: float = 0, to_time: float = None, multiplier: float = 10) -> np.array:
		"""
		:param from_time: starting time of statistical data from "dump" file (seconds)
		:param to_time: ending time of statistical data from "dump" file (seconds)
		:param multiplier: of congestion indexes (otherwise, values between 0 and 1)
		:return: array of congestion indexes (averaged over intervals)
		"""
		xml_file: XmlFile = XmlFile(self.options.data_path)
		assert(xml_file.is_loaded())
		to_time = to_time if to_time is not None else float("inf")
		if from_time < 0:
			print(f"Intervals from data file cannot start at time: {from_time} < 0 !")
			return None
		elif from_time > to_time:
			print(f"Time interval has to be in the form <from, to>, but from: {from_time} > to: {to_time} !")
			return None
		elif xml_file.root.find("interval") is None:
			print("Cannot find element 'interval' in data file!")
			return None
		# Edge_id : CongestionIndex
		ci_map: Dict[str, float] = {edge_id: 0 for edge_id in self.graph.road_network.edges}
		n_intervals: int = 0
		for interval in xml_file.root.findall("interval"):
			if float(interval.attrib["begin"]) < from_time:
				continue
			elif float(interval.attrib["end"]) > to_time:
				break
			n_intervals += 1
			for edge in interval.findall("edge"):
				if edge.attrib["id"] not in ci_map:
					continue
				ci_map[edge.attrib["id"]] += float(edge.attrib["congestionIndex"])
		# Average the congestion indexes, increase to avoid 0-values and multiply
		return ((np.array(list(ci_map.values())) / n_intervals) + 0.001) * multiplier

	def choose_clusters(self, size: int = 200) -> Dict[int, List[int]]:
		"""
		:param size: of cluster member to be picked, default 100
		:return: clusters which satisfy the given size requirement
		"""
		return {k: v for k, v in self.clusters.items() if len(v) > size}


if __name__ == "__main__":
	config: dict = JsonFile.load_config(get_args().get("config"))
	if not config or config is None:
		raise ValueError("Received invalid config!")
	clustering: GravClustering = GravClustering(GravClusteringOptions.dataclass_from_dict(GravClusteringOptions, config))
	clustering.run(clustering.options.iterations, clustering.options.plotting.frequency, clustering.options.merging_radius)
