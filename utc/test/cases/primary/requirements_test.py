import unittest
import pkg_resources
from pathlib import Path


class TestRequirements(unittest.TestCase):
    """Test availability of required packages."""

    def test_requirements(self) -> None:
        """
        Test that each required package is available.

        :return: None
        """
        _REQUIREMENTS_PATH = Path(__file__).parent.parent.parent.parent.with_name("requirements.txt")
        # Ref: https://stackoverflow.com/a/45474387/
        requirements = pkg_resources.parse_requirements(_REQUIREMENTS_PATH.open())
        for requirement in requirements:
            requirement = str(requirement)
            with self.subTest(requirement=requirement):
                pkg_resources.require(requirement)
        requirements.close()
