from utc.src.utils.xml_object import XmlObject
from typing import Tuple, List, Dict, Any


class Edge(XmlObject):
    """ Class describing Edge of road network from SUMO '.net.xml' file """

    def __init__(self, attributes: Dict[str, str], lanes: Dict[str, Dict[str, Any]], internal_id: int):
        """
        :param attributes: attributes extracted from xml element
        :param lanes: xml elements of edge lanes
        :param internal_id: internal if of object
        """
        super().__init__("edge", attributes["id"], internal_id, attributes)
        self.from_junction: str = self.attributes["from"]
        self.to_junction: str = self.attributes["to"]
        self.speed: float = round(lanes[next(iter(lanes))]["speed"], 3)
        self.length: float = round(lanes[next(iter(lanes))]["length"], 3)
        self.references: int = 0  # Number of references to this object (by Routes)
        self.lanes: Dict[str, Dict[str, Any]] = lanes

    # ------------------------------------------ Getters ------------------------------------------

    def get_junctions(self) -> List[str]:
        """
        :return: Starting and ending junctions of edge
        """
        return [self.from_junction, self.to_junction]

    def get_lane_count(self) -> int:
        """
        :return: number of lanes on Edge
        """
        return len(self.lanes.keys())

    def get_centroid(self) -> Tuple[float, float]:
        """
        :return: center of gravity of edge defined by lane shape's,
        since not every edge has shape, but has at least 1 lane
        """
        x_coord: float = 0
        y_coord: float = 0
        coord_count: int = 0
        for lane_params in self.lanes.values():
            for (x, y) in lane_params["shape"]:  # [[x, y], [x, y], ...]
                x_coord += x
                y_coord += y
            coord_count += len(lane_params["shape"])
        return round(x_coord / coord_count, 3), round(y_coord / coord_count, 3)

    def get_travel_time(self, speed: float = None) -> float:
        """
        :param speed: the speed we want to compute travel time for (If none, max speed is used -> free flow)
        :return: travel time on edge, 3 digit precision
        """
        speed = self.speed if speed is None else speed
        assert(speed > 0)
        return round(self.length / speed, 3)

    # ------------------------------------------ Utils ------------------------------------------

    def info(self, verbose: bool = True) -> str:
        ret_val: str = (
            f"Edge: {self.get_id(False)}({self.get_id()}), from: '{self.from_junction}', to: '{self.to_junction}'"
        )
        if not verbose:
            return ret_val
        ret_val += f" ref: {self.references}, attributes: {self.attributes}"
        return ret_val

    def travel(self) -> Tuple[str, float]:
        """
        :return: Tuple containing destination junction id and length
        """
        return self.to_junction, self.length
