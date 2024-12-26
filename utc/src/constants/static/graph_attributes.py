from typing import Dict, List, Any, Callable

# ---------------------------------------------------- Methods ----------------------------------------------------


def process_shape(shape: str) -> List[List[float]]:
    """
    :param shape: extracted from xml object -> "x1,y1 x2,y2 ..."
    :return: array of coordinates forming shape -> [(x1, y1), ...]
    """
    return [list(map(float, i.split(","))) for i in shape.split()]


def filter_attributes(attributes: Dict[str, str], by: Dict[str, Callable]) -> Dict[str, Any]:
    """
    :param attributes: extracted from xml object
    :param by: attributes we want to keep (mapped to function transforming them to correct type)
    :return: filtered dictionary of attributes
    """
    return {key: by[key](value) for key, value in attributes.items() if key in by}

# ---------------------------------------------------- Attributes ----------------------------------------------------


class EdgeAttributes:
    """
    Class containing constant variables for default (wanted)
    attributes of edges (including lines and their type e.g. int, float, ...)
    """
    LANE_WIDTH: int = 1
    LINES_STYLE: str = "solid"
    EDGE_ATTRIBUTES: Dict[str, Callable] = {
        "id": str, "from": str, "to": str,
        "type": str, "shape": process_shape
    }
    LANE_ATTRIBUTES: Dict[str, Callable] = {
        "id": str, "length": float, "speed": float, "shape": process_shape
    }


class NodeAttributes:
    """
    Class containing constant variables for default (wanted)
    attributes of nodes (including junctions and their type e.g. int, float, ...)
    """
    NODE_SIZE: int = 3  # radius squared of node
    NODE_LABEL_SIZE: int = 6  # text size of nodes label
    JUNCTION_ATTRIBUTES: Dict[str, Callable] = {
        "id": str, "type": str, "x": float, "y": float
    }
