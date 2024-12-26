from typing import List, Union, Optional
from os import rename, remove
from os.path import isfile, relpath
from pathlib import Path
from io import TextIOWrapper, BufferedWriter, BufferedReader, BufferedRandom


class MyFile:
    """
    Class handling file behaviour, enables opening of files
    ("with MyFile(file_path, mode) as file .."),
    provides static and utility functions, acts as an
    super class to other file classes.
    """
    def __init__(self, file_path: str, mode: str = "w+", extension: str = ""):
        """
        :param file_path: path to file (can be either full path, or file_name,
        for file_name subclasses of MyFile must implement 'get_file_path' method)
        :param mode: mode to open file with, only necessary when opening the file:
        e.g. "with MyFile(path, 'r') as file", default -> "w+" (read & write)
        :param extension: extension of file (will be checked if its present in 'file_path'),
        default None
        """
        self.file_path: str = ""  # Absolute path of file
        self.dir_path: str = ""
        self.mode: str = mode  # Mode for opening file
        self.extension: str = extension  # Default file extension
        self.load(file_path)

    # ------------------------------------------- Load & Save -------------------------------------------

    def load(self, file_path: str) -> bool:
        """
        Also functions as "setter" of file_path attribute

        :param file_path: path to file (can be new file_name, or an existing one
        or name of file which specific subclasses of MyFile class can load
        from pre-defined directories)
        :return: True on success, false otherwise
        """
        self.file_path = file_path
        self.dir_path = str(Path(self.file_path).parent)
        # Load existing file
        if self.file_exists(self.file_path, message=False):
            # print(f"Loading existing file: '{self.file_path}'")
            return True
        try:
            # File does not exist, try to load from name (class specific directory)
            self.file_path = self.get_known_path(self.get_file_name(file_path))
            if not self.file_exists(self.file_path, message=False):
                self.file_path = file_path  # Assuming new file name
            else:
                self.dir_path = str(Path(self.file_path).parent)
                return True
        except NotImplementedError:
            return False
        return False

    def save(self, file_path: str = "default") -> bool:
        """
        :param file_path: path to file, if equal to 'default',
        classes parameter file_path will be used
        :return: Saves file to previously entered path,
        serves as interface method for custom saving
        """
        raise NotImplementedError("Method 'save' must be defined by subclasses of MyFile!")

    # ------------------------------------------- Utils -------------------------------------------

    def reload(self) -> None:
        """
        Loads file again from the set path

        :return: None
        """
        self.load(self.file_path)

    def set_mode(self, mode: str) -> None:
        """
        :param mode: of file to be used when opened
        :return: None
        """
        self.mode = mode

    def is_loaded(self) -> bool:
        """
        :return: true if file representing this class exists, false otherwise
        """
        return self.file_exists(self.file_path, message=False)

    def get_known_path(self, file_name: str) -> str:
        """
        :param file_name: name of file (automatically called with name of file in 'load' method)
        :return: full path to file (Subclass specific), original parameter if file was not found
        """
        raise NotImplementedError(
            "Error, to load file from specific file names, method"
            " 'get_known_path' must be implemented by subclasses of MyFile class!"
        )

    def get_name(self) -> str:
        """
        :return: name of file without extension
        """
        return self.get_file_name(self)

    # ------------------------------------------- Static methods -------------------------------------------

    @staticmethod
    def remove_file_extension(file_path: Union[str, 'MyFile']) -> str:
        """
        :param file_path: path to file (either string or MyFile class)
        :return: List of file extensions
        """
        # Convert to string if file_path is MyFile class instance
        return str(Path(str(file_path)).with_suffix(""))

    @staticmethod
    def get_file_extension(file_path: Union[str, 'MyFile']) -> List[str]:
        """
        :param file_path: path to file (either string or MyFile class)
        :return: List of file extensions
        """
        # Convert to string if file_path is MyFile class instance
        return Path(str(file_path)).suffixes

    @staticmethod
    def get_file_name(file_path: Union[str, 'MyFile']) -> str:
        """
        :param file_path: path to file (either string or MyFile class)
        :return: name of file without extension
        """
        # Convert to string if file_path is MyFile class
        file_path = str(file_path)
        # File without extension
        if Path(file_path).suffix == "":
            return Path(file_path).stem
        # Loop until suffix is removed
        while Path(file_path).suffix != "":
            file_path = Path(file_path).stem
        return file_path

    @staticmethod
    def get_absolute_path(file_path: Union[str, 'MyFile']) -> str:
        """
        :param file_path: path to file (either string or MyFile class)
        :return: name of file without extension
        """
        # Convert to string if file_path is MyFile class
        return str(Path(str(file_path)).parent.resolve())

    @staticmethod
    def file_exists(file_path: Union[str, 'MyFile'], message: bool = True) -> bool:
        """
        :param file_path: path to file (either string or MyFile class)
        :param message: bool, prints "file file_path does not exists" if file does not exist
        :return: True if file exists, false otherwise
        """
        # Convert to string if file_path is MyFile class
        ret_val = isfile(str(file_path))
        if message and not ret_val:
            print(f"File: '{file_path}' does not exist!")
        return ret_val

    @staticmethod
    def rename_file(original: Union[str, 'MyFile'], target: Union[str, 'MyFile'], message: bool = False) -> bool:
        """
        :param original: path to existing file (either string or MyFile class)
        :param target: name of new file
        :param message: true if message about success renaming should be printed, default false
        :return: true if renaming was successful, false otherwise
        :raises FileNotFoundError if file "original" does not exist
        """
        # Checks
        if not MyFile.file_exists(original, message=False):
            raise FileNotFoundError(f"File: {original} does not exist!")
        try:
            rename(str(original), str(target))
            if isinstance(original, MyFile):  # Change name of original file
                original.file_path = str(target)
        except OSError as e:
            print(f"Error: {e} occurred during renaming of file: '{original}'")
            return False
        if message:
            print(f"Successfully change name of file: '{original}' -> '{target}'")
        return True

    @staticmethod
    def delete_file(file_path: Union[str, 'MyFile']) -> bool:
        """
        :param file_path: path to file (either string or MyFile class)
        :return: true on success, false otherwise
        """
        if not MyFile.file_exists(file_path):
            return False
        try:
            remove(file_path)
        except OSError as e:
            print(f"During deletion of file: '{file_path}', error occurred: '{e}'")
            return False
        # print(f"Successfully deleted file: '{file_path}'")
        return True

    @staticmethod
    def get_relative_path(target: str, origin: str) -> str:
        """
        Creates relative path from given paths, e.g.:\n
        target = /data/scenarios/test/additional/routes/test_routes.rou.xml, \n
        origin = /data/scenarios/test2/simulation/config \n
        result = ../../../test/additional/routes/test_routes.rou.xml

        :param target: file to which we want to create the relative path
        :param origin: the current path (should end with directory, not file!)
        :return: Relative path of files
        """
        return Path(relpath(target, origin)).as_posix()

    @staticmethod
    def resolve_relative_path(origin: str, relative_path: str) -> str:
        """
        Resolves relative path from given origin, e.q.:\n
        origin = .../data/scenarios/test/simulation/config, \n
        relative = ../../additional/routes, \n
        result = .../data/scenarios/test/additional/routes

        :param origin: of file
        :param relative_path: of file (if its already full path, it will be returned)
        :return: Resolved relative path, as absolute path
        """
        return Path(origin, relative_path).resolve().as_posix()

    # ------------------------------------------- Magic methods -------------------------------------------

    def __str__(self) -> str:
        """
        :return: full path to file
        """
        return self.file_path

    def __enter__(self) -> Optional[Union[TextIOWrapper, BufferedWriter, BufferedReader, BufferedRandom]]:
        """
        :return: opened file, None if file does not exist
        """
        # Make file_pointer inaccessible outside
        self._file_pointer: Optional[Union[TextIOWrapper, BufferedWriter, BufferedReader, BufferedRandom]] = None
        if not self.file_path.endswith(self.extension):
            print(f"Expecting file to be of type: '{self.extension}', got: '{self.file_path}' !")
            return self._file_pointer
        try:  # Check for errors
            self._file_pointer = open(self.file_path, self.mode)
        except OSError as e:
            print(f"Error: '{e}' occurred during opening of file: '{self.file_path}'")
        return self._file_pointer

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        :return: Closes file pointer if its not None
        """
        # Error
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, traceback)
        # Close file
        if self._file_pointer is not None:
            try:  # Check for errors
                self._file_pointer.close()
            except OSError as e:
                print(f"Error: '{e}' occurred during closing of file: '{self.file_path}'")
