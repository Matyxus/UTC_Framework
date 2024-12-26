from utc.src.constants.file_system.my_file import MyFile
from os import listdir, mkdir, rmdir
from os.path import isdir, isfile
from typing import Optional, List


class MyDirectory:
    """
    Class representing directory in file system, provides method to work with directories,
    including static utility methods.
    """
    def __init__(self, path: str):
        """
        :param path: to directory parent folder (can be string format)
        """
        self.name: str = MyFile.get_file_name(path)
        self.dir_path: str = path

    # ------------------------------------------- Sub-dirs -------------------------------------------

    def create_sub_dir(self, subdir_name: str) -> Optional['MyDirectory']:
        """
        :param subdir_name: name of subdirectory
        :return: DefaultDir class if creation of directory was successful, None otherwise
        """
        sub_dir: MyDirectory = MyDirectory(self.dir_path + "/" + subdir_name)
        return sub_dir if sub_dir.initialize_dir() else None

    def delete_sub_dir(self, subdir_name: str, recursive: bool = False) -> bool:
        """
        :param subdir_name: name of directory to be deleted
        :param recursive:  if the whole directory tree should be deleted (False by default)
        :return: True on success, false otherwise
        """
        return self.delete_directory(self.dir_path + "/" + subdir_name, recursive)

    def get_sub_dir(self, subdir_name: str) -> Optional['MyDirectory']:
        """
        :param subdir_name: name of subdirectory
        :return: MyDirectory class, None if directory does not exist
        """
        if not self.dir_exist(self.dir_path + "/" + subdir_name):
            return None
        return MyDirectory(self.dir_path + "/" + subdir_name)

    def has_subdir(self, subdir_name: str, message: bool = False) -> bool:
        """
        :param subdir_name: name of subdirectory
        :param message: if prints for debugging should be displayed
        :return: True if directory exists, false otherwise
        """
        return self.dir_exist(self.dir_path + "/" + subdir_name, message)

    # ------------------------------------------- Utils -------------------------------------------

    def initialize_dir(self) -> bool:
        """
        :return: true if directory does not exist (and was made), false otherwise
        """
        return self.make_directory(self.dir_path)

    def is_loaded(self, message: bool = True) -> bool:
        """
        :param message: if prints for debugging should be displayed
        :return: True if directory exists, false otherwise
        """
        return self.dir_exist(self.dir_path, message)

    def get_file(self, file_name: str) -> Optional[str]:
        """
        :param file_name: name of file (with extension)
        :return: Path to file, None if file does not exist
        """
        file_name = self.dir_path + "/" + file_name
        if not MyFile.file_exists(file_name):
            return None
        return file_name

    def list_dir(
            self, full_path: bool = False,
            extension: bool = True, sort: bool = False,
            only_files: bool = False, only_dirs: bool = False
         ) -> Optional[List[str]]:
        """
        :param full_path: if full path should be kept (False by default)
        :param extension: if extension of files should be kept (true by default)
        :param sort: True if files should be sorted (False by default - no sorting - random os order)
        :param only_files: True if only files should be listed (False by default)
        :param only_dirs: True if only directories should be listed (False by default)
        :return: List of files in directory, None if directory does not exist
        """
        return self.list_directory(self.dir_path, full_path, extension, sort, only_files, only_dirs)

    def format_file(self, file_name: str) -> str:
        """
        :param file_name: name of file (with extension)
        :return: string of formatted file with path in this directory
        """
        return self.dir_path + "/" + file_name

    # ------------------------------------------- Static methods -------------------------------------------

    @staticmethod
    def make_directory(dir_path: str) -> bool:
        """
        :param dir_path: of directory to be created
        :return: true if directory was created, false otherwise
        """
        try:
            mkdir(dir_path)
        except OSError as e:
            # Already exists
            if isinstance(e, FileExistsError):
                return True
            print(f"Unable to create directory: '{dir_path}', error: '{e}'")
            return False
        return True

    @staticmethod
    def delete_directory(dir_path: str, recursive: bool = False, message: bool = True) -> bool:
        """
        :param dir_path: of directory to be deleted (including files in directory)
        :param recursive: if the whole directory tree should be deleted (False by default)
        :param message: if message about directory not existing should be printed, default true
        :return: true on success, false otherwise
        """
        if not MyDirectory.dir_exist(dir_path, message):
            return False
        elif recursive:  # Check to not delete anything important!
            assert("scenarios" in dir_path and not dir_path.endswith("scenarios"))
        try:
            for file in MyDirectory.list_directory(dir_path, True, True):
                if isfile(file) and not MyFile.delete_file(file):
                    return False
                elif isdir(file) and recursive:
                    MyDirectory.delete_directory(file, True, True)
            rmdir(dir_path)
        except (OSError, NotImplementedError) as e:
            print(f"Unable to delete directory: '{dir_path}', got error: '{e}'")
            return False
        return True

    @staticmethod
    def dir_exist(dir_path: str, message: bool = True) -> bool:
        """
        :param dir_path: of directory to be checked
        :param message: optional argument, (default True), if message 'Directory .. does not exist' should be printed
        :return: true if directory exists, false otherwise
        """
        if isinstance(dir_path, str) and isdir(dir_path):
            return True
        elif message:
            print(f"Directory: {dir_path} does not exist!")
        return False

    @staticmethod
    def list_directory(
            dir_path: str, full_path: bool = False,
            extension: bool = True, sort: bool = False,
            only_files: bool = False, only_dirs: bool = False
        ) -> Optional[List[str]]:
        """
        :param dir_path: of directory we want to list
        :param full_path: if full path should be kept (False by default)
        :param extension: if extension of files should be kept (true by default)
        :param sort: True if files should be sorted (False by default - no sorting - random os order)
        :param only_files: True if only files should be listed (False by default)
        :param only_dirs: True if only directories should be listed (False by default)
        :return: list of files & directories in directory, None if directory does not exist
        """
        if not MyDirectory.dir_exist(dir_path):
            return None
        elif only_files and only_dirs:
            print(f"Error, cannot list directory without files and directories!")
            return None
        ret_val: List[str] = listdir(dir_path)
        # Filter files or directories
        if only_files:
            ret_val = [file for file in ret_val if isfile(file)]
        elif only_dirs:
            ret_val = [directory for directory in ret_val if isdir(directory)]
        # Other utils
        if full_path:  # Add full path
            ret_val = [dir_path + "/" + name for name in ret_val]
        if sort:  # Sort files and or directories
            ret_val.sort()
        if not extension and not only_dirs:  # Remove extension from files
            return [(MyFile.remove_file_extension(file) if isfile(file) else file) for file in ret_val]
        return ret_val


