from utc.src.routing.planning.mode import Mode, PddlOptions, RoadNetwork
from utc.src.routing.pddl.pddl_episode import PddlEpisode, PddlProblem, PddlResult
from utc.src.routing.planning.scheduler import Scheduler
from utc.src.simulator.vehicle import Vehicle, VehicleEntry
from utc.src.simulator.simulation import Simulation, traci
from copy import deepcopy
from typing import Optional, List, Set, Tuple, Dict


class Flags:
    UNKNOWN: int = -1
    MISSED: int = 0
    SCHEDULED: int = 1


class Online(Mode):
    """ Class representing 'online' mode of planning """
    def __init__(self, options: PddlOptions):
        super().__init__(options)
        self.entry: Optional[VehicleEntry] = None
        self.sub_network: RoadNetwork = self.problem_generator.network_builder.sub_graph.road_network
        self.travel_times: Dict[str, float] = {}
        self.etas: Dict[str, Tuple[float, float, int]] = {}
        self.actual: Dict[str, float] = {}

    def generate_episodes(self) -> List[PddlEpisode]:
        episodes: List[PddlEpisode] = []
        vehicle_queue: Set[str] = set()  # Vehicles being considered for planning
        planning_vehicles: Set[str] = set()  # Vehicles scheduled for planning
        planned_vehicles: Set[str] = set()  # Already planned vehicles
        arrived_vehicles: Set[str] = set()
        # int(self.options.planning.window / self.scenario.config_file.get_step_length())
        steps: int = int(10 / self.scenario.config_file.get_step_length())
        assert(steps == 20)
        region = self.sub_network.edges.keys()
        options: Dict[str, str] = {
            "--save-state.rng": "",
            "-W": ""
        }
        counter: int = 0
        to_plan: int = 0
        missed_vehicles: int = 0
        for edge in self.graph.road_network.edges.values():
            self.travel_times[edge.id] = edge.get_travel_time()

        with Simulation(self.scenario.config_file, options) as simulation:
            while simulation.is_running():
                # planning_vehicles ^= (planning_vehicles & planned_vehicles)
                print(f"Current time: {simulation.get_time(False)}")
                # Simulation stopped during advancement
                if not self.advance(simulation):
                    break


                # After each time-step go over vehicles, and estimate if they are able to arrive
                # within X seconds to the region (if they already arrived, remove them from queue)
                for vehicle_id in vehicle_queue:
                    if vehicle_id not in arrived_vehicles:
                        eta: float = self.estimate_arrival(vehicle_id)
                        flag: int = Flags.UNKNOWN
                        # Evaluate it next time, the data will be too imprecise for now
                        if eta >= 20:
                            continue
                        elif eta < 10:
                            flag = Flags.MISSED
                        else:
                            flag = Flags.SCHEDULED
                        self.etas[vehicle_id] = (simulation.get_time(False), eta, flag)
                    # else:
                    #     missed_vehicles += 1
                planning_vehicles |= vehicle_queue
                vehicle_queue ^= (vehicle_queue & self.etas.keys())
                vehicle_queue ^= (vehicle_queue & arrived_vehicles)
                counter += 1
                if counter > 100:
                    break
        good: Tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)
        worse: Tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)
        bad: Tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)
        for vehicle, arrival_time in self.actual.items():
            if vehicle not in self.etas:
                continue
            diff = abs((self.etas[vehicle][0] + self.etas[vehicle][1]) - arrival_time)
            flag = (self.etas[vehicle][-1] == Flags.MISSED)
            over_estimated: bool = (self.etas[vehicle][0] + self.etas[vehicle][1]) > arrival_time
            if diff < 10:
                good = (good[0]+1, good[1] + (not over_estimated), good[2] + over_estimated, good[3] + flag, good[4] + (not flag))
            elif diff < 20:
                worse = (worse[0]+1, worse[1] + (not over_estimated), worse[2] + over_estimated, worse[3] + flag, worse[4] + (not flag))
            else:
                bad = (bad[0]+1, bad[1] + (not over_estimated), bad[2] + over_estimated, bad[3] + flag, bad[4] + (not flag))
        print(f"Performance after {counter} steps for {len(self.actual)} vehicles")
        print(f"{good, worse, bad}, planned: {to_plan}, missed: {missed_vehicles}")
        print(f"Under estimated: {good[1]+worse[1]+bad[1]}, over: {good[2]+worse[2]+bad[2]}")
        print(f"Missed: {good[3]+worse[3]+bad[3]}, scheduled: {good[4]+worse[4]+bad[4]}")
        quit()
        return episodes

    # -------------------------------------------- Simulation --------------------------------------------

    def advance(self, simulation: Simulation) -> bool:
        """
        :return:
        """
        # Simulate to future and observe vehicles
        for _ in range(steps):
            simulation.step()
            arrived_vehicles |= set(traci.simulation.getArrivedIDList())
            # Find all vehicles which just departed and drive on sub-region, add them to queue
            for vehicle_id in traci.simulation.getDepartedIDList():
                assert (vehicle_id not in planned_vehicles and vehicle_id not in vehicle_queue)
                route_edges: Tuple[str] = traci.vehicle.getRoute(vehicle_id)
                # Make sure vehicle does not start inside the region
                if (set(route_edges) & region) and route_edges[0] not in region:
                    vehicle_queue.add(vehicle_id)
            # For each ETA vehicle, check if it arrived and the diff
            for vehicle_id in planning_vehicles:
                if vehicle_id not in arrived_vehicles:
                    if traci.vehicle.getRoadID(vehicle_id) in region:
                        planned_vehicles.add(vehicle_id)
                        self.actual[vehicle_id] = simulation.get_time(False)
                else:
                    self.actual[vehicle_id] = simulation.get_time(False)
        # Update average travel time on edges
        for edge in self.graph.road_network.edges.keys():
            self.travel_times[edge] = (self.travel_times[edge] + traci.edge.getTraveltime(edge)) / 2
        return True


    def generate_problem(self, planning_vehicles: Set[str], simulation: Simulation) -> Optional[PddlProblem]:
        """
        :return:
        """
        assert(simulation is not None and simulation.is_running(use_end_time=False))
        interval: Tuple[int, int] = (
            int(simulation.get_time() - self.options.planning.window), int(simulation.get_time())
        )
        # Create vehicle entry to be added to planning
        entry: VehicleEntry = VehicleEntry(interval)
        for vehicle in self.scenario.vehicles_file.get_elements("vehicle", planning_vehicles):
            entry.vehicles[vehicle.attrib["id"]] = Vehicle(deepcopy(vehicle.attrib))
        assert (len(entry.vehicles.keys()) == len(planning_vehicles))
        for route in self.scenario.routes_file.get_elements("route", set(vehicle.attributes["route"] for vehicle in entry.vehicles.values())):
            entry.original_routes[route.attrib["id"]] = deepcopy(route)
        self.entry = entry
        return self.problem_generator.generate_problem(entry, f"problem_{interval[0]}_{interval[1]}", self.options.planning.domain)

    # ------------------------------- Utils -------------------------------

    def init(self) -> None:
        """
        :return:
        """
        pass

    def estimate_arrival(self, vehicle_id: str) -> float:
        """
        :param vehicle_id:
        :return:
        """
        # print(f"Estimating arrival of vehicle: '{vehicle_id}'")
        route: Tuple[str] = traci.vehicle.getRoute(vehicle_id)
        index: int = traci.vehicle.getRouteIndex(vehicle_id)
        # print(f"Route: '{route}'")
        # print(f"Current edge(id): '{index}' <-> '{route[index]}'")
        # Find the first edge in the region
        sub_index, sub_edge = None, None
        for i, edge in enumerate(route):
            if edge in self.sub_network.edges:
                sub_index, sub_edge = i, edge
                break
        # print(f"Region index: '{sub_index}', edge: '{sub_edge}'")
        # print(f"Path till region: '{route[index:sub_index]}'")
        # print(f"Path to be traveled: '{route[index+1:sub_index-1]}'")
        # Estimate the arrival time
        # traci.edge.getTraveltime()
        # self.travel_times[edge.id]
        eta: float = sum([self.travel_times[edge.id] for edge in self.graph.road_network.get_edges(route[index:sub_index])])
        # print(f"Naive ETA: {eta}")
        # quit()
        return eta


    def save_result(self, episode: PddlEpisode, free_mem: bool = True) -> bool:
        """
        :param episode: to be saved (i.e. vehicles and their new routes)
        :param free_mem: True if memory of episode should be freed (network, vehicles, etc.)
        :return: True on success, false otherwise
        """
        # Check episode
        if episode is None or episode.problem is None:
            print("Error, received invalid episode!")
            return False
        for (vehicle, route) in self.parser.process_result(episode).items():
            route_id: str = self.new_scenario.routes_file.add_route(route, re_index=True)
            vehicle.attrib["route"] = route_id
            self.new_scenario.vehicles_file.add_vehicle(vehicle)
            orig_route = episode.problem.container.vehicles[vehicle.attrib['id']].original_route
            orig_edges: List[str] = orig_route.attrib["edges"].split()
            if not (tuple(orig_edges) == traci.vehicle.getRoute(vehicle.attrib['id'])):
                print(f"Vehicle: {vehicle.attrib['id']}")
                print(f"Orig route: {tuple(orig_edges)}")
                print(f"Traci route: {traci.vehicle.getRoute(vehicle.attrib['id'])}")
                print(f"Equal id: {traci.vehicle.getRouteID(vehicle.attrib['id']) == orig_route.attrib['id']}")
                if traci.vehicle.getRouteID(vehicle.attrib['id']) in self.entry.original_routes:
                    print(f"Entry route: {self.entry.original_routes[traci.vehicle.getRouteID(vehicle.attrib['id'])].attrib['edges']}")
                else:
                    print("Entry route: None!")
                raise ValueError("Error")
            self.assign_route(vehicle.attrib['id'], route.attrib["edges"].split())
        if free_mem:
            episode.free_mem()
        return True

    def assign_route(self, vehicle_id: str, edges: List[str]) -> bool:
        """
        :param vehicle_id: to which route is assigned
        :param edges: route
        :return: True on success, False otherwise
        """
        # Perform some checks
        assert (edges[0] == traci.vehicle.getRoute(vehicle_id)[0])
        assert (edges[-1] == traci.vehicle.getRoute(vehicle_id)[-1])
        try:
            route_index: int = traci.vehicle.getRouteIndex(vehicle_id)
            if route_index >= 0:
                current_edge: str = traci.vehicle.getRoute(vehicle_id)[route_index]
                if current_edge in edges:
                    traci.vehicle.setRoute(vehicle_id, edges[edges.index(current_edge):])
                else:
                    print(f"Vehicle departed at: {traci.vehicle.getDeparture(vehicle_id)}")
                    print(f"Current time: {traci.simulation.getTime()}")
                    print(f"New route: {edges}")
                    print(f"Index: {route_index}")
                    print(f"{traci.vehicle.getRoute(vehicle_id)}")
                    print(f"Error at vehicle: {vehicle_id}, missing edge in route")
                    return False
            else:  # Vehicle has not yet departed, route can be assigned entirely
                traci.vehicle.setRoute(vehicle_id, edges)
        except traci.exceptions.TraCIException as e:
            print(f"Error: {e}")
            return False
        return True


# for edge_id in region:
#     edge = self.sub_network.get_edge(edge_id)
#     edge.attributes["travelTime"] = edge.get_travel_time()
# Start simulation and planning
#     # Update travel time
#     for edge_id in region:
#         self.sub_network.get_edge(edge_id).attributes["travelTime"] += traci.edge.getTraveltime(edge_id)
# # Average observed travel time
# for edge_id in region:
#     self.sub_network.get_edge(edge_id).attributes["travelTime"] /= (steps+1)
#     self.sub_network.get_edge(edge_id).attributes["travelTime"] = max(
#         self.sub_network.get_edge(edge_id).attributes["travelTime"], 1
#     )
# if len(planning_vehicles) >= 10:
#     problem: PddlProblem = self.generate_problem(planning_vehicles, simulation)
#     assert(problem is not None)
#     result: Optional[PddlResult] = self.result_generator.generate_results(
#         [problem], self.options.planning.domain,
#         self.options.planning.planner,
#         self.new_scenario.scenario_dir,
#         self.options.planning.timeout
#     )[0]
#     # Generate episode, save to file and assign new routes to running vehicles
#     episodes.append(PddlEpisode(counter, problem, result))
#     self.save_result(episodes[-1], free_mem=True)
#     counter += 1
# Continue simulation to the previous end-point
# else:
#     print(f"Too few vehicles for planning, skipping ...")

# Generate problem from found vehicles
# if planning_vehicles:
#     print(f"Starting planning for: {len(planning_vehicles)} vehicles.")
#     vehicle_queue ^= planning_vehicles
#     planned_vehicles |= planning_vehicles
#     planning_vehicles.clear()
# else:
#     print("No vehicles entered sub-region")



