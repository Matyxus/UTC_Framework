from utc.src.constants.static.file_constants import DirPaths, FileExtension
from utc.src.constants.file_system.file_types.xml_file import XmlFile
from utc.src.graph.graph import Graph, RoadNetwork


class DataFormatter:
    """
    Class formatting networks and edge dumps files to fit
    representation where edge and junction id's are integers (from 0 to N).
    Provides method to add Congestion Index parameter to edge dump files.
    """
    def __init__(self):
        pass

    # ------------------------ Congestion Index ------------------------

    def compute_congestion_index(self, data_file: str, network: str, save: bool = True) -> bool:
        """
        Congestion index (CI) = (actual travel time - free flow travel time) / free flow travel time,
        formula used here to have CI between <0, 1> is: 1 - (free flow travel time / actual travel time ).

        :param data_file: path to data file (edge dump)
        :param network: network from which to extract the maximal speed on edges
        :param save: true if congestion index should be saved in original data file
        :return: True on success, false otherwise
        :raises FileNotFoundError: if files do not exist
        """
        xml_file: XmlFile = XmlFile(data_file)
        if not xml_file.is_loaded():
            raise FileNotFoundError(f"Edge dump: '{data_file}' does not exist!")
        graph: Graph = Graph(RoadNetwork())
        assert(graph.loader.load_map(network))
        # Compute congestion index
        print("Computing congestion indexes")
        for count, node in enumerate(xml_file.root.findall("interval")):
            # print(f"Computing CI for interval: {count}")
            for edge in node.findall("edge"):
                if "traveltime" in edge.attrib and float(edge.attrib["traveltime"]) > 0:
                    # Free flow travel time
                    ftt: float = graph.road_network.get_edge(edge.attrib["id"]).get_travel_time()
                    # Actual travel time
                    att: float = float(edge.attrib["traveltime"])
                    if att <= ftt:  # In case vehicle were faster or as fast as possible (given max speed limit)
                        edge.attrib["congestionIndex"] = "0.0"
                    else:
                        edge.attrib["congestionIndex"] = str(round(1 - (ftt / att), 3))
                        assert(0 <= float(edge.attrib["congestionIndex"]) <= 1)
                else:  # No travel time was observed here
                    edge.attrib["congestionIndex"] = "0"
        print("Finished computing congestion indexes")
        return True if not save else xml_file.save(xml_file.file_path)

    def congestion_difference(self, edge_data1: str, edge_data2: str, new_file: str) -> bool:
        """
        Creates new file, with congestion index difference, both files must it already
        calculated, and must be from the same network.

        :param edge_data1: path to edge data with congestion index already calculated
        :param edge_data2: path to edge data with congestion index already calculated
        :param new_file: name of new file
        :return: true on success, false otherwise
        """
        # Compute congestion index
        print("Computing congestion index difference")
        xml_file1: XmlFile = XmlFile(edge_data1)
        xml_file2: XmlFile = XmlFile(edge_data2)
        if not xml_file1.is_loaded() or not xml_file2.is_loaded():
            return False
        intervals1: list = list(xml_file1.root.findall("interval"))
        intervals2: list = list(xml_file2.root.findall("interval"))
        # if len(intervals1) != len(intervals2):
        #     print("Intervals of edge data files are not equal !")
        #     print(f"E1: {edge_data1}, E2: {edge_data2}")
        #     quit()
        #     return False
        if len(intervals1) != len(intervals2):
            print("Intervals of edge data files are not equal !")
            if len(intervals1) > len(intervals2):
                intervals1 = intervals1[:len(intervals2)]
            else:
                intervals2 = intervals1[:len(intervals1)]

        for index, (interval1, interval2) in enumerate(zip(intervals1, intervals2)):
            # print(f"Computing CI difference for interval: {index}")
            if len(interval1.findall("edge")) != len(interval2.findall("edge")):
                print("Intervals have different number of edges !")
                return False
            for edge1, edge2 in zip(interval1.findall("edge"), interval2.findall("edge")):
                assert("congestionIndex" in edge1.attrib and "congestionIndex" in edge2.attrib)
                edge1.attrib["congestionIndex"] = str(
                    round(float(edge1.attrib["congestionIndex"]) - float(edge2.attrib["congestionIndex"]), 3)
                )
        print("Finished computing congestion index difference")
        return xml_file1.save(new_file)


if __name__ == "__main__":
    # DataFormatter().compute_congestion_index(
    #     DirPaths.SCENARIO_STATISTICS.format("lust_25200_32400") + "/stats_full_edgedata.out.xml",
    #     "lust"
    # )
    DataFormatter().compute_congestion_index(
        DirPaths.SCENARIO_STATISTICS.format("itsc_25200_32400_planned") + "/stats_full_edgedata.out.xml",
        "DCC"
    )
