from utc.src.routing.pddl.base.pddl_problem import PddlProblem


class VehicleDomain:
    """
    Class holding representation of vehicles for '.pddl' problem files
    """
    def __init__(self):
        # Name of group used by vehicles
        self.vehicle_group_name: str = "car"

    def process_vehicles(self, problem: PddlProblem) -> bool:
        """
        Adds vehicles to ':object' and adds their initial and
        destination positions to ':init' & ':goal'

        :param problem: instance of pddl problem
        :return: True on success, false otherwise
        """
        for pddl_vehicle in problem.container.get_planned_vehicles():
            # Object definition
            problem.add_object(self.vehicle_group_name, pddl_vehicle.pddl_id)
            # Initial position (dynamic)
            problem.add_init_state(f"(at {pddl_vehicle.pddl_id} {pddl_vehicle.starting_junction})")
            # Destination pos (static)
            problem.add_init_state(f"(togo {pddl_vehicle.pddl_id} {pddl_vehicle.ending_junction})")
            # Goal position (static)
            problem.add_goal_state(f"(at {pddl_vehicle.pddl_id} {pddl_vehicle.ending_junction})")
        return True
