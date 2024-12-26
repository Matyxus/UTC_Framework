from utc.src.constants.file_system import JsonFile, FilePaths
from utc.src.plan_qd.parameters.parameter import Parameter
from utc.src.constants.file_system import FilePaths
from typing import Dict


class PddlParameters(Parameter):
    """
    Class representing pddl parameters used for sessions of
    scenarios generation
    """
    def __init__(self, file_path: str = "default"):
        super().__init__(FilePaths.PDDL_TEMPLATES.format("default_pddl") if file_path == "default" else file_path)

    # ------------------------------ Utils ------------------------------

    def get_planner(self) -> str:
        """
        :return: name of planner
        """
        return self.objects["planner"]

    def get_timeout(self) -> int:
        """
        :return: time given for planner execution
        """
        return self.objects["timeout"]

    def get_domain(self) -> str:
        """
        :return: name of pddl domain
        """
        return self.objects["domain"]

    def get_window(self) -> int:
        """
        :return: snapshot of simulation from which problem files are created
        """
        return self.objects["window"]

    def get_known_path(self, file_name: str) -> str:
        if self.file_exists(FilePaths.PDDL_TEMPLATES.format(file_name), message=False):
            return FilePaths.PDDL_TEMPLATES.format(file_name)
        return file_name

    def check_data(self) -> bool:
        checks: Dict[str, callable] = {
            "planner": str,
            "timeout": int,
            "domain": str,
            "window": int,
        }
        for object_name, object_type in checks.items():
            if object_name not in self.objects or not isinstance(object_type, object_type):
                return False
        return True


# For testing purposes
if __name__ == "__main__":
    temp: PddlParameters = PddlParameters()
    temp.load_data()
    print(temp.get_window())
    # print(type(temp.load_data()["timeout"]))

