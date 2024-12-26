from utc.src.constants.static import FileExtension
from utc.src.constants.file_system.file_types.xml_file import XmlFile, Element
from typing import Iterator, Dict, List, Union, Optional


class DumpFile(XmlFile):
    """
    File class handling ".out.xml" (edge dump) files,
    provides utility methods
    """
    def __init__(self, file_path: str):
        """
        :param file_path: to ".out.xml" file
        """
        super().__init__(file_path, extension=FileExtension.EDGE_DUMP)

    # ------------------------------------------ Getters ------------------------------------------

    def get_interval(self, from_time: float, to_time: float = None) -> Optional[Iterator[Element]]:
        """
        :param from_time: starting time in hours (0-24) of interval, e.g. 15.30 (4:30 PM).
        :param to_time:  starting time in hours of interval, if value is not set (None), returns
        only interval starting at 'from_time'
        :return: generator of found intervals (can be only 1)
        """
        # File is not loaded
        to_time = (from_time + 0.5) if to_time is None else to_time
        if not self.is_loaded():
            print(f"Xml file is not loaded, cannot return intervals!")
            return None
        # End time has to be at least equal to start time
        elif not from_time <= to_time:
            return None
        # Hours must be non negative
        elif from_time < 0 or to_time < 0:
            return None
        # Transform hours into seconds
        start_interval_index: float = from_time * 3600
        end_interval_index: float = to_time * 3600
        # Find all xml elements named "junction"
        for interval in self.root.findall("interval"):
            # Return interval in correct time
            if (start_interval_index <= float(interval.attrib["begin"])
                    and end_interval_index >= float(interval.attrib["end"])):
                yield interval
            elif float(interval.attrib["end"]) > end_interval_index:
                break

    # ------------------------------------------ Utils  ------------------------------------------

    def sum_attribute(
            self, intervals: Union[Iterator[Element], List[Element]],
            attribute: str, average: bool = False
        ) -> Dict[str, float]:
        """
        :param intervals: extracted from dump file
        :param attribute: name of attribute to be summed
        :param average: if values should be averaged (divided by number of intervals), default False
        :return: Sum of attributes (mapping edge_id to values) over all given intervals
        """
        intervals = list(intervals) if not isinstance(intervals, list) else intervals
        count: int = len(intervals)
        if count == 0:
            print(f"Received empty list of intervals!")
            return {}
        # Compute
        ret_val: Dict[str, float] = {edge.attrib["id"]: 0 for edge in intervals[0].findall("edge")}
        for interval in intervals:
            for edge in interval.findall("edge"):
                ret_val[edge.attrib["id"]] += float(edge.attrib.get(attribute, 0))
        # Check for average
        if not average or count == 1:
            return ret_val
        return {k: (v / count) for k, v in ret_val.items()}

    def get_known_path(self, file_name: str) -> str:
        return file_name
