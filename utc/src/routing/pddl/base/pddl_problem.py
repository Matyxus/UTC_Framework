from utc.src.constants.static import FileExtension
from utc.src.routing.pddl.base.pddl_struct import PddlStruct
from utc.src.routing.pddl.base.vehicle_container import VehicleContainer
from utc.src.routing.pddl.info.episode_info import ProblemInfo
from utc.src.graph import RoadNetwork
from typing import Optional


class PddlProblem(PddlStruct):
    """
    Class extending PddlStruct by ':domain', 'problem', ':metric',
    holds other classes defining pddl problem files, provides
    methods to create pddl problem files while holding all the
    necessary objects to create them (network, vehicles, etc.).
    """
    def __init__(
            self, name: str, domain: str,
            metric: str = "minimize (total-cost)",
            network: Optional[RoadNetwork] = None,
            vehicles: Optional[VehicleContainer] = None
        ):
        """
        :param name: of problem
        :param domain: of the problem
        :param metric: metric defining the problem (cost minimization by default)
        :param network: road network on which vehicle will be routed
        :param vehicles: container of vehicles which will be routed
        """
        super().__init__()
        # Pddl attributes
        self.name: str = name
        self.domain: str = domain
        self.metric: str = metric
        # Objects of pddl problem
        self.network: Optional[RoadNetwork] = network
        self.container: Optional[VehicleContainer] = vehicles
        self.info: ProblemInfo = ProblemInfo(self.name)

    # ------------------------------------ Utils ------------------------------------

    def save(self, file_path: str) -> bool:
        """
        :param file_path: path to file which will be created
        :return: True on success, false otherwise
        """
        # Checks
        if self.network is None or self.container is None:
            print("Error invalid type!")
            return False
        elif not file_path.endswith(FileExtension.PDDL):
            file_path += FileExtension.PDDL
        # Conversion to pdl
        print(f"Creating pddl problem: '{self.name}' in: '{file_path}'")
        self.add_init_state("(= (total-cost) 0)")  # Initial situation current cost is 0
        try:
            with open(file_path, "w") as pddl_problem_file:
                pddl_problem_file.write(str(self))
        except OSError as e:
            print(f"Error: '{e}' while generating pddl problem file: {file_path}!")
            return False
        print(f"Successfully created pddl problem file: {file_path}")
        self.info.problem_finished()
        self.clear()
        return True

    def is_valid(self) -> bool:
        """
        :return: True if this class instance is valid PDDL problem, false otherwise
        """
        return self.network is not None and self.container is not None

    # ------------------------------------ Magic Methods ------------------------------------

    def __str__(self) -> str:
        """
        :return: Pddl problem as string -> https://planning.wiki/ref/pddl/problem
        """
        ret_val: str = "(define\n"
        ret_val += f"(problem {self.name})\n"
        ret_val += f"(:domain {self.domain})\n"
        ret_val += super().__str__()
        ret_val += f"(:metric {self.metric})\n"
        return ret_val + ")"
