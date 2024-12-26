import unittest
from utc.src.converter import Converter
from utc.src.utils.constants import PATH, file_exists


class ConverterTest(unittest.TestCase):
    """ Test Converter class by converting ".osm" file into ".net.xml" """

    def test_converter(self) -> None:
        """
        Tests Converter class by converting simple ".osm"
        network called "example.osm" into ".net.xml" network

        :return: None
        """
        temp: Converter = Converter()
        # Check if "osmfilter" exists
        if not file_exists(PATH.OSM_FILTER, message=False):
            if not file_exists(PATH.OSM_FILTER + ".c", message=False):
                raise FileNotFoundError(
                    f"File: {PATH.OSM_FILTER} does not exist, download 'osmfilter.c' from: \n"
                    f"https://wiki.openstreetmap.org/wiki/Osmfilter \n"
                    f"into folder: {PATH.OSM_FILTER.replace('osmfilter', '')} and compile with command:\n"
                    f"'gcc osmfilter.c -O3 -o osmfilter'\n"
                )
            raise FileNotFoundError(
                f"File: {PATH.OSM_FILTER} does not exist, compile {PATH.OSM_FILTER + '.c'} into {PATH.OSM_FILTER}\n"
                "using command: 'gcc osmfilter.c -O3 -o osmfilter'"
            )
        # Check if "example.osm" exists
        elif not file_exists(PATH.ORIGINAL_OSM_MAP.format("example"), message=False):
            raise FileNotFoundError(f"File: {PATH.ORIGINAL_OSM_MAP.format('example')} does not exist!")
        temp.convert("example")
        # Check if "_filtered.osm" and ".net.xml" files got generated
        assert (file_exists(PATH.FILTERED_OSM_MAP.format("example")))
        assert (file_exists(PATH.NETWORK_SUMO_MAP.format("example")))
