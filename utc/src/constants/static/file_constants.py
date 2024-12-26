from pathlib import Path


# ---------------------------------- Extension ----------------------------------
class FileExtension:
    """ Class holding extension of files """
    PDDL: str = ".pddl"
    XML: str = ".xml"
    JSON: str = ".json"
    CSV: str = ".csv"
    LOG: str = ".log"
    # ------- Simulation & Scenarios -------
    SUMO_ROUTES: str = ".rou.xml"  # Files containing vehicle routes
    SUMO_ADDITIONAL: str = ".add.xml"  # Additional files (such as vehicles)
    SUMO_CONFIG: str = ".sumocfg"  # (is of xml type)
    SUMO_STATS: str = ".stat.xml"  # statistics file
    # ------- Maps -------
    OSM: str = ".osm"
    SUMO_NETWORK: str = ".net.xml"
    EDGE_DUMP: str = ".out.xml"


# ---------------------------------- CWD ----------------------------------
def _initialize_cwd() -> str:
    """
    :raise ValueError: in case directory 'utc' cannot be found in path
    :return: absolute path to project root ('UTC/utc')
    """
    cwd: Path = Path(__file__)
    if "utc" not in str(cwd):
        raise ValueError(
            "Location of 'file_constants.py' file is incorrect,"
            f" unable to find 'utc' in '{str(cwd)}' !"
        )
    while not str(cwd).endswith("utc"):
        cwd = cwd.parent
    return str(cwd)

# -------------------------------------------- Paths --------------------------------------------


class DirPaths:
    """
    Class holding different project paths for directories, used with .format(args) (not always),
    where args is the name of directory
    """
    CWD: str = _initialize_cwd()  # Project Root (UTC/utc)
    # Logs & configs
    LOGS: str = (CWD + "/data/logs")
    CONFIG: str = (CWD + "/data/config")
    # Domain & planners
    PDDL_DOMAINS: str = (CWD + "/data/domains")
    PDDL_PLANNERS: str = (CWD + "/data/planners/{0}")
    # Templates
    XML_TEMPLATES: str = (CWD + "/data/templates/xml")
    JSON_TEMPLATES: str = (CWD + "/data/templates/json")
    # -------------------------------------- Maps --------------------------------------
    MAPS: str = (CWD + "/data/maps")  # Path to folder containing folders related to maps
    MAPS_OSM: str = (MAPS + "/osm")  # Path to folder containing maps from open street map (".osm")
    MAPS_SUMO: str = (MAPS + "/sumo")  # Path to folder containing ".net.xml" maps for SUMO
    # -------------------------------------- Scenarios --------------------------------------
    SCENARIO: str = (CWD + "/data/scenarios/{0}")
    # Pddl
    PDDL_PROBLEMS: str = (SCENARIO + "/problems")
    PDDL_RESULTS: str = (SCENARIO + "/results")
    # Additional files (routes, vehicles, networks, flows, ...)
    SCENARIO_ADDITIONAL: str = (SCENARIO + "/additional")
    # Simulation
    SCENARIO_STATISTICS: str = (SCENARIO + "/statistics")
    SCENARIO_CONFIGS: str = (SCENARIO + "/config")
    SCENARIO_INFOS: str = (SCENARIO + "/information")
    # Planner output
    SCENARIO_PLANNER_OUTS: str = (SCENARIO + "/output")


class FilePaths:
    """
    Class holding different project paths for files, used with '.format(args)' (not always),
    where args is usually the name of file (without extension)
    """
    OSM_FILTER: str = (DirPaths.CWD + "/data/osm_filter/osmfilter")  # Path to osmfilter (executable)
    # -------------------------------------- Logs & Configs --------------------------------------
    LOG_FILE: str = (DirPaths.LOGS + "/{0}" + FileExtension.LOG)
    CONFIG_FILE: str = (DirPaths.CONFIG + "/{0}" + FileExtension.JSON)
    # -------------------------------------- Maps --------------------------------------
    # Path to file from open street map (".osm")
    MAP_OSM: str = (DirPaths.MAPS_OSM + "/{0}" + FileExtension.OSM)
    # Path to '.net.xml' file map for SUMO
    MAP_SUMO: str = (DirPaths.MAPS_SUMO + "/{0}" + FileExtension.SUMO_NETWORK)
    # --------------------------------------  Pddl --------------------------------------
    PDDL_DOMAIN: str = (DirPaths.PDDL_DOMAINS + "/{0}" + FileExtension.PDDL)
    # Path scenarios specific pddl problem file
    PDDL_PROBLEM: str = (DirPaths.PDDL_PROBLEMS + "/{1}" + FileExtension.PDDL)
    # Path scenarios specific pddl result file
    PDDL_RESULT: str = (DirPaths.PDDL_RESULTS + "/{1}" + FileExtension.PDDL)
    # -------------------------------------- Scenarios --------------------------------------
    SCENARIO_ROUTES: str = (DirPaths.SCENARIO_ADDITIONAL + "/{1}" + FileExtension.SUMO_ROUTES)
    SCENARIO_VEHICLES: str = (DirPaths.SCENARIO_ADDITIONAL + "/{1}_vehicles" + FileExtension.SUMO_ADDITIONAL)
    SCENARIO_ADDITIONAL: str = (DirPaths.SCENARIO_ADDITIONAL + "/{1}" + FileExtension.SUMO_ADDITIONAL)
    SCENARIO_SNAPSHOT: str = (DirPaths.SCENARIO_ADDITIONAL + "/{1}_snapshot" + FileExtension.XML)
    # Path to '.sumocfg' file specific to scenario
    SCENARIO_CONFIG: str = (DirPaths.SCENARIO_CONFIGS + "/{1}" + FileExtension.SUMO_CONFIG)
    # Path to '.json' file specific to scenario
    SCENARIO_INFO: str = (DirPaths.SCENARIO_INFOS + "/{1}" + FileExtension.JSON)
    # Path to '.stat.xml' file specific to scenario
    SCENARIO_STATISTICS: str = (DirPaths.SCENARIO_STATISTICS + "/{1}" + FileExtension.SUMO_STATS)
    # -------------------------------------- Templates --------------------------------------
    JSON_SCHEMA: str = (DirPaths.JSON_TEMPLATES + "/{0}" + FileExtension.JSON)

    class XmlTemplates:
        """ Class defining XML templates """
        SUMO_CONFIG: str = (DirPaths.XML_TEMPLATES + "/sumo_config" + FileExtension.SUMO_CONFIG)
        SUMO_ROUTES: str = (DirPaths.XML_TEMPLATES + "/sumo_routes" + FileExtension.SUMO_ROUTES)
        SUMO_VEHICLE: str = (DirPaths.XML_TEMPLATES + "/sumo_vehicles" + FileExtension.SUMO_ADDITIONAL)
        EDGE_DATA: str = (DirPaths.XML_TEMPLATES + "/edge_data" + FileExtension.SUMO_ADDITIONAL)

