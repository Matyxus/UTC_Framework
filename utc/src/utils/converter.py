from utc.src.constants.static import FilePaths, DirPaths
from utc.src.constants.file_system import MyFile, MyDirectory
from utc.deprecated.ui import UserInterface, Command
from utc.src.utils.options import NetConvertOptions
from typing import Set


class Converter(UserInterface):
	"""
	Class converting ".osm" (OpenStreetMap) files into ".net.xml" files which SUMO can use.
	Does so by using osm filter to filter non-road like objects (except traffic lights),
	and afterwards uses netconvert (program from SUMO) to generate ".net.xml" file,
	Converter does not support logging of commands (since they are the same every time)
	"""

	def __init__(self, log_commands: bool = False):
		super().__init__("converter", log_commands)

	#  --------------------------------------------  Commands  --------------------------------------------

	def initialize_commands(self) -> None:
		super().initialize_commands()
		self.user_input.add_command([Command("convert", self.convert_command)])

	@UserInterface.log_command
	def convert_command(self, file_name: str) -> None:
		"""
		Expecting file to be in directory defined in constants.PATH.ORIGINAL_OSM_MAP,
		converts osm file into '.net.xml' file, while removing all
		non-highway elements from original osm file.

		:param file_name: name of '.osm' file, to convert (if used 'all', whole
		directory will be converted)
		:return: None
		"""
		to_convert: Set[str] = set()
		if file_name == "all":
			to_convert = set(MyDirectory.list_directory(DirPaths.MAPS_OSM, keep_extension=False))
			if not to_convert:
				print(f"Directory of {DirPaths.MAPS_OSM} is either empty or does not exist!")
				return
		else:
			to_convert = {file_name}
		# Convert files
		for file_name in to_convert:
			print(f"Converting map: '{file_name}'")
			if not self.osm_filter(file_name):
				continue
			self.net_convert(file_name)

	def osm_filter(self, map_name: str) -> bool:
		"""
		Uses osm filter to filter ".osm" file, removing all non-road like objects
		(except traffic lights). Filtered file will be saved in directory
		'/utc/data/maps/filtered' under the same name

		:param map_name: name of ".osm" map (located in '/utc/data/maps/osm')
		:return: True if successful, false otherwise
		"""
		print("Filtering osm file with osm_filter")
		file_path: str = FilePaths.MAP_OSM.format(map_name)
		print(f"File path: {file_path}")
		if not MyFile.file_exists(file_path):
			return False
		filtered_file_path: str = FilePaths.MAP_FILTERED.format(map_name)
		if MyFile.file_exists(filtered_file_path, message=False):
			print(f"Filtered file of: {map_name} already exists")
			return True
		command: str = (FilePaths.OSM_FILTER + " " + file_path)
		# osmfilter arguments
		command += (
			' --hash-memory=720 --keep-ways="highway=primary =tertiary '
			'=residential =primary_link =secondary =secondary_link =trunk =trunk_link =motorway =motorway_link" '
			'--keep-nodes= --keep-relations='
		)
		command += (" -o=" + filtered_file_path)
		success, output = self.call_shell(command)
		if success:
			print(f"Done filtering osm file: '{map_name}', saved in: '{filtered_file_path}'")
		return success

	def net_convert(self, map_name: str) -> bool:
		"""
		Uses netconvert to convert ".osm" files into ".net.xml",
		expecting ".osm" file to be already filtered (by 'osm_filter' method),
		located in directory '/utc/data/maps/filtered'. Resulting network file will be
		saved in directory '/utc/data/maps/sumo'

		:param map_name: name of OSM map (filtered by osmfilter)
		:return: True if successful, false otherwise
		"""
		print("Creating '.net.xml' file for SUMO with netconvert on filtered file")
		file_path: str = FilePaths.MAP_FILTERED.format(map_name)
		if not MyFile.file_exists(file_path):
			return False
		net_file_path: str = FilePaths.MAP_SUMO.format(map_name)
		if MyFile.file_exists(net_file_path, message=False):
			print(f"Network file of: {map_name} already exists")
			return True
		net_convert: NetConvertOptions = NetConvertOptions()
		success = net_convert.convert_network(file_path, net_file_path)
		if success:
			print(f"Done creating network file: '{map_name}, saved in: {net_file_path}")
		return success


if __name__ == "__main__":
	converter: Converter = Converter(log_commands=True)
	converter.run()
