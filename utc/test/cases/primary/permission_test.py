import unittest
from os import mkdir, rename, remove, rmdir
from utc.deprecated.ui import UserInterface


class PermissionTest(unittest.TestCase):
    """
    Class testing permissions to manipulate files, directories,
    calling commands from shell/cmd
    """

    def test_file_permission(self) -> None:
        """
        Tests file creation, renaming, deletion

        :return: None
        """
        # Test file creation
        with open("test_file", "w") as file:
            # write into file
            file.write("Hello World\n")
        # Test renaming file
        rename("test_file", "test_file")
        # Test file deletion
        remove("test_file")

    def test_dir_permission(self) -> None:
        """
        Tests directory creation, deletion

        :return: None
        """
        # Test dir creation
        mkdir("test_dir")
        # Test dir deletion
        rmdir("test_dir")

    def test_shell(self) -> None:
        """
        Tests method of UserInterface class calling subprocess.check_output

        :return: None
        """
        temp: UserInterface = UserInterface()
        success, output = temp.call_shell("netconvert --help")
        assert (success and output is not None)







