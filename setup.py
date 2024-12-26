from setuptools import setup, find_packages

try:
    setup(name='UTC', version='2.0', python_requires='>=3.9', packages=find_packages())
finally:
    # Initialize data directory in /utc
    from os import mkdir
    data_path: str = "utc/data"
    dirs_to_make: list = [
        # Data
        data_path,
        data_path + "/domains",  # Domains
        data_path + "/logs",  # Logs (made by logging)
        data_path + "/planners",  # Folder containing pddl planners (must be added by user)
        data_path + "/scenarios",  # Folder containing SUMO scenarios
        data_path + "/config",  # Folder containing configuration files
        # Maps
        data_path + "/maps",
        data_path + "/maps/osm",  # Folder containing ".osm" maps downloaded from OpenStreetMap
        data_path + "/maps/sumo"  # Folder containing ".net.xml" maps created by netedit from "maps/filtered" maps
    ]
    # Create directories
    print("Creating 'data' directories for project")
    for directory in dirs_to_make:
        try:
            mkdir(directory)
        except FileExistsError as e:
            # Directory already exists
            continue
    print("Finished creating directories")
