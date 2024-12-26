from utc.src.routing.pddl.base.pddl_problem import PddlProblem, VehicleContainer
from utc.src.routing.pddl.pddl_options import NetworkOptions
from utc.src.routing.traffic.network_builder import NetworkBuilder
from utc.src.routing.pddl.domains.network_domain import NetworkDomain
from utc.src.routing.pddl.domains.vehicle_domain import VehicleDomain
from utc.src.graph import Graph
from utc.src.simulator.scenario import Scenario
from utc.src.simulator.vehicle.vehicle_entry import VehicleEntry
from typing import Optional


class ProblemGenerator:
    """
    Class handling the generation of pddl problem files
    """
    def __init__(self, new_scenario: Scenario, options: NetworkOptions, graph: Graph, sub_graph: Graph = None):
        """
        :param new_scenario: new scenario in which pddl problems are saved
        :param options: options of network
        :param sub_graph: on which pddl files will be generated on and vehicles drive on (default graph
        is one given in configuration file of scenario)
        """
        assert(new_scenario is not None and new_scenario.scenario_dir.is_loaded())
        self.new_scenario: Scenario = new_scenario
        self.network_builder: NetworkBuilder = NetworkBuilder(graph, sub_graph, options)
        self.network_domain: NetworkDomain = NetworkDomain()
        self.vehicle_domain: VehicleDomain = VehicleDomain()

    def generate_problem(self, entry: VehicleEntry, name: str, domain: str, save: bool = True) -> Optional[PddlProblem]:
        """
        :param entry: vehicle entry containing vehicles to be routed
        :param name: of the pddl problem
        :param domain: of the pddl problem
        :param save: True if pddl problem should be instantly saved (i.e. if pddl problem file gets created)
        :return: PddlProblem class if successful, None otherwise
        """
        if entry is None or not entry.vehicles:
            print(f"Error, cannot generate pddl problem: '{name}', invalid vehicles!")
            return None
        vehicles: VehicleContainer = VehicleContainer(entry)
        network = self.network_builder.build_network(vehicles)
        if network is None:
            print(f"Unable to formulate pddl problem: '{name}', no vehicles scheduled for planning!")
        vehicles.network = network
        problem: PddlProblem = PddlProblem(name, domain, network=network, vehicles=vehicles)
        if save and not self.save_problem(problem, self.new_scenario.scenario_dir.problems.format_file(name)):
            print(f"Unable to save pddl problem: '{name}'")
        return problem

    def save_problem(self, problem: PddlProblem, file_path: str) -> bool:
        """
        :param problem: to be saved
        :param file_path: path in which the file will be saved
        :return: True on success, false otherwise
        """
        if problem is None:
            return False
        elif not problem.container.schedule_task():
            return False
        network_success: bool = self.network_domain.process_graph(problem)
        vehicle_success: bool = self.vehicle_domain.process_vehicles(problem)
        if not (network_success and vehicle_success):
            raise ValueError(
                f"Error while creating pddl representation of vehicles or network of problem: '{problem.name}'"
            )
        return problem.save(file_path)

