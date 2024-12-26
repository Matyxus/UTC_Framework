from utc.src.constants.dynamic.arguments import get_args
from utc.src.constants.file_system.file_types.json_file import JsonFile
from utc.src.constants.file_system.file_types.xml_file import XmlFile
from utc.src.clustering.gravitational.grav_clustering_options import GravClusteringOptions
from utc.src.graph import Graph, RoadNetwork
from typing import Dict, List, Union
import numpy as np
import matplotlib.pyplot as plt


class Grid:
	def __init__(self):
		self.rows: int = 0
		self.cells: int = 0
		self.size: int = 0
		self.cells: list = []
		self.sortedCells: list = []
		self.gridMap: list = []
		self.binCounts: list = []
		self.pointOrder: list = []
		self.neighbours: list = []
		self.alive: list = []
		self.min_x: float = float("inf")
		self.min_y: float = float("inf")
		self.max_x: float = float("-inf")
		self.max_y: float = float("-inf")

	def is_valid(self, cell_id: int) -> bool:
		"""
		:param cell_id:
		:return:
		"""
		return 0 <= cell_id < self.size


class State:
	def __init__(self):
		self.numEdges: int = 0
		self.positions: np.array = None
		self.weights: np.array = None
		# Indexes for lowering size -> so that we can index weights and positions
		self.indexes: list = []
		self.merges: list = []
		self.clusters: list = []


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
		self.clusters: Dict[int, List[int]] = {}  # edge_id : [edge_id, ...]
		self.color_map = plt.get_cmap("hsv")([0.1 * i for i in range(11)])
		self.grid: Grid = Grid()
		self.state: State = State()
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
		# ----------- State -----------
		self.state.positions = np.matrix.round(self.create_centroid_matrix(), decimals=3)  # Nx2
		self.state.weights = np.matrix.round(self.create_ci_matrix(start_time, end_time), decimals=3)
		self.state.indexes = list(self.clusters.keys())
		self.state.merges = list(self.clusters.keys())
		self.state.clusters = list(self.clusters.keys())
		self.state.numEdges = len(self.clusters)
		# ----------- Grid -----------
		self.initialize_grid()
		# ----------- Points -----------
		print("Finished initializing all variables")

	def initialize_grid(self) -> None:
		print("Initializing grid!")
		# ------- Compute bounding box of grid -------
		min_x, min_y, max_x, max_y = float("inf"), float("inf"), float("-inf"), float("-inf")
		for (x, y) in self.state.positions:
			min_x = min(min_x, x)
			min_y = min(min_y, y)
			max_x = max(max_x, x)
			max_y = max(max_y, y)
		self.grid.min_x, self.grid.min_y, self.grid.max_x, self.grid.max_y = min_x, min_y, max_x, max_y
		# ((Max X - Min X) * (Max Y - Min Y)) / r
		self.grid.rows = int(np.ceil((max_x - min_x) / self.options.merging_radius))
		self.grid.cols = int(np.ceil((max_y - min_y) / self.options.merging_radius))
		self.grid.size = (self.grid.rows * self.grid.cols)
		print(f"New grid limits are: (({self.grid.min_x, self.grid.min_y}),({self.grid.max_x, self.grid.max_y}))")
		print(f"Rows, cols: ({self.grid.rows, self.grid.cols}) -> {self.grid.size}")
		self.grid.cells = [0] * self.state.numEdges
		self.grid.sortedCells = [0] * self.state.numEdges
		self.grid.pointOrder = [0] * self.state.numEdges
		self.grid.alive = [True] * self.state.numEdges
		self.grid.gridMap = [0] * self.grid.size
		self.grid.binCounts = [0] * self.grid.size
		self.grid.neighbours = [
			-1, 1, self.grid.rows, self.grid.rows + 1,
			self.grid.rows - 1, -self.grid.rows, -self.grid.rows - 1, -self.grid.rows + 1
		]
		self.insert_points()

	def insert_points(self) -> None:
		"""
		:return:
		"""
		print("Inserting points to grid")
		# Compute cell for each edge and increase bit counts
		for i in range(self.state.numEdges):
			self.grid.cells[i] = self.get_cell(i)
			self.grid.pointOrder[i] = self.grid.binCounts[self.grid.cells[i]]
			self.grid.binCounts[self.grid.cells[i]] += 1
		# Compute prefix scan
		for i in range(self.grid.size - 1):
			self.grid.gridMap[i+1] = (self.grid.gridMap[i] + self.grid.binCounts[i])
		# Sort array by prefix scan
		for i in range(self.state.numEdges):
			self.grid.sortedCells[self.grid.gridMap[self.grid.cells[i]] + self.grid.pointOrder[i]] = i
		return

	# ------------------------------------------ Clustering ------------------------------------------

	def run(self, iterations: int = 200, plot_freq: int = 10, merging_radius: float = 15.0) -> None:
		"""
		:param iterations: number of total iteration to be done
		:param plot_freq: how often should be plot displayed, default every 50 iterations
		:param merging_radius: minimal distance between clusters centers to merge them, default 15 (meters)
		:return: None
		"""
		if not np.all(self.state.weights >= 0):
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
		# ------------------ Clustering ------------------
		print("Finding nearest neighbour for each point ...")
		# For each edge find its closes neighbour
		x, y = 0, 0
		neigh_x, neigh_y = 0, 0
		min_dist = float("inf")
		for i in range(self.state.numEdges):
			self.state.merges[i] = -1  # Reset to default
			min_dist = float("inf")
			x, y = self.state.positions[i]
			cell_id: int = self.grid.cells[i]
			index = self.grid.gridMap[cell_id]
			# Go over neighbours in the same cell
			if self.grid.binCounts[cell_id] > 1:
				for j in range(self.grid.binCounts[cell_id]):
					neigh = self.grid.sortedCells[index + j]
					if neigh == i:
						continue
					neigh_x, neigh_y = self.state.positions[neigh]
					dst = np.square(x - neigh_x) + np.square(y - neigh_y)
					if dst < merging_radius and dst < min_dist:
						self.state.merges[i] = neigh
						min_dist = dst
			# Go over neighbours in different cells
			for shift in self.grid.neighbours:
				neigh_cell: int = cell_id + shift
				if not self.grid.is_valid(neigh_cell):
					continue
				index = self.grid.gridMap[neigh_cell]
				for j in range(self.grid.binCounts[neigh_cell]):
					neigh = self.grid.sortedCells[index + j]
					neigh_x, neigh_y = self.state.positions[neigh]
					dst = np.square(x - neigh_x) + np.square(y - neigh_y)
					if dst < merging_radius and dst < min_dist:
						self.state.merges[i] = neigh
						min_dist = dst
				# while index < self.state.numEdges and self.grid.cells[self.grid.sortedCells[index]] == neigh_cell:
				# 	neigh = self.grid.sortedCells[index]
				# 	neigh_x, neigh_y = self.state.positions[neigh]
				# 	dst = np.square(x-neigh_x) + np.square(y-neigh_y)
				# 	if dst < merging_radius and dst < min_dist:
				# 		self.state.merges[i] = neigh
				# 		min_dist = dst
				# 	index += 1
		# ------------------ Merging ------------------
		print("Merging nearest neighbour's in radius ...")
		# Merge those who are symmetrically merged
		# (can be checked solely by the smaller index) and second condition
		merges: int = 0
		for i in range(self.state.numEdges):
			neigh: int = self.state.merges[i]
			# Only lower index performs the merging, so as to not merge twice
			if neigh > i == self.state.merges[neigh]:
				# Merge clusters together, make the merging one "dead"
				self.grid.alive[neigh] = False
				self.state.weights[i] += self.state.weights[neigh]
				self.state.clusters[neigh] = i
				merges += 1
		x, y = self.state.positions[4877]
		neigh_x, neigh_y = self.state.positions[4878]
		dst = np.square(x - neigh_x) + np.square(y - neigh_y)
		print(f"Distance between 4877 & 4878 -> {np.sqrt(dst)}")
		neigh_x, neigh_y = self.state.positions[3880]
		dst = np.square(x - neigh_x) + np.square(y - neigh_y)
		print(f"Distance between 4877 & 3880 -> {np.sqrt(dst)}")
		print(f"Total merges: {merges}, alive cells: {sum(self.grid.alive)}/{self.state.numEdges}")
		# ------------------ Re-indexing ------------------
		print("Re-indexing ...")
		# Lets say from the starting numEdges we have reached the nearest 2^x,
		# decrease the size of array & numEdges to match this, create new indexing array containing only
		# those pointID's which are alive.
		prefix = [0] * (self.state.numEdges + 1)
		for i in range(1, (self.state.numEdges + 1)):
			prefix[i] = prefix[i - 1] + self.grid.alive[i - 1]
		# print(f"Prefix last 40: {prefix[-40:]}")
		assert(prefix[-1] == sum(self.grid.alive))
		new_indexes = [0] * prefix[-1]
		for i in range(self.state.numEdges):
			if prefix[i] != prefix[i + 1]:
				new_indexes[prefix[i]] = self.state.indexes[i]
		# Check
		for i in new_indexes:
			assert(self.grid.alive[i])
		# print(f"New indexes: {new_indexes}")
		quit()
		# self.state.positions = self.state.positions[np.array(self.state.indexes)]
		quit()
		# ------------------ Calculate movement of edges based on grav. attraction ------------------
		print("Calculating movements of edges ... ")
		movements: np.array = np.zeros((self.state.positions.shape[0], 2), dtype=np.float32)
		for i in range(self.state.positions.shape[0]):
			# Squared distances, gravity requires distance to be squared
			distances: np.array = np.sum(np.square(self.state.positions - [self.state.positions[i]]), axis=1)
			distances[i] = 1
			assert(0 not in distances)
			attraction: np.array = self.state.weights / distances
			movements[i] = np.matrix.round(np.dot((self.state.positions - self.state.positions[i]).T, attraction), 5)
		self.state.positions += movements
		print(f"Calculating clustering of edges")
		# ----------------------- Insert points again -----------------------
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
		# print(f"Congestion matrix shape: {self.state.weights.shape}")

		def get_colors() -> np.ndarray:
			"""
			:return: numpy array of colors, Reds if temperature is not chosen
			"""
			if not temperature:
				return plt.get_cmap("Reds")(self.state.weights / 10)
			# Create arrays to store colors
			colors: np.ndarray = np.zeros(self.state.weights.shape + (4,))  # RGBA colors
			# Apply colormap for values in the range [0, 1]
			colors[self.state.weights >= 0] = plt.cm.Reds(self.state.weights[self.state.weights >= 0] / 10)
			# Apply reversed colormap for values in the range [-1, 0]
			colors[self.state.weights < 0] = plt.cm.Blues(-(self.state.weights[self.state.weights < 0] / 10))
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
		ax.scatter(self.state.positions[:, 0], self.state.positions[:, 1], s=self.state.weights)
		ax.set_title(title)
		self.graph.display.show_plot(ax, save_path)

	# ------------------------------------------ Utils ------------------------------------------

	def get_cell(self, edge_id: int) -> int:
		"""
		:param edge_id:
		:return:
		"""
		assert(edge_id < self.state.numEdges)
		x: int = int((self.state.positions[edge_id][0] - self.grid.min_x) / self.options.merging_radius)
		y: int = int((self.state.positions[edge_id][1] - self.grid.min_y) / self.options.merging_radius)
		assert(0 <= x + y * self.grid.rows < self.grid.size)
		return x + y * self.grid.rows

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
	config: dict = JsonFile.load_config("clustering_dcc_config")
	if not config or config is None:
		raise ValueError("Received invalid config!")
	clustering: GravClustering = GravClustering(GravClusteringOptions.dataclass_from_dict(GravClusteringOptions, config))
	clustering.run(clustering.options.iterations, clustering.options.plotting.frequency, clustering.options.merging_radius)
