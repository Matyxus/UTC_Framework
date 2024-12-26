from utc.src.semestral.evolutionary import (Algorithm, ALGORITHMS, Population)
from utc.src.constants.static import FilePaths, DirPaths, check_process_count
from utc.src.constants.file_system import XmlFile, MyDirectory
from utc.src.simulator import Scenario, Simulation
from utc.src.semestral.tl_constants import SEED, WINDOW, MIN_GREEN_TIME, YELLOW_DURATION
from utc.src.semestral.traffic_lights import TrafficLights
from utc.src.semestral.worker import evaluate, sim_evaluate, sim_log
from typing import Optional, Union, Tuple, Set, Dict
import multiprocessing
import time
from math import ceil
from copy import deepcopy
from typing import List
import traci
import numpy as np


class TrafficLightOptimization:
    """
    Class implementing TrafficLightOptimization in SUMO.
    """
    def __init__(self, scenario_name: str, options: dict):
        """
        :param scenario_name: name of scenario to be optimized
        :param options: general options (processes, seed, ...)
        """
        self.scenario: Scenario = Scenario(scenario_name)
        self.traffic_lights: List[TrafficLights] = []
        self.algorithm: Optional[Algorithm] = None
        # Round up in case window is not divisible by minimal green time
        self.cycle_phases: int = ceil(WINDOW / (MIN_GREEN_TIME + YELLOW_DURATION))
        # Current snapshot of simulation (state which should be loaded)
        self.snapshot: str = ""
        self.current_time: float = 0  # Current simulation time
        # Currently running simulation
        self.options: dict = options
        self.simulation_options: dict = {}

    def main(self, alg_options: dict, sim_options: dict) -> bool:
        """
        :param alg_options: options for algorithm
        :param sim_options: options for simulation
        :return: True on success, false otherwise
        """
        np.random.seed(SEED)
        print(f"Initializing simulation and algorithm, options: {sim_options}, {alg_options}")
        # -------- Init --------
        # Check options for algorithm
        if "algorithm" not in alg_options or alg_options["algorithm"] not in ALGORITHMS:
            print(f"Missing or unknown option: 'algorithm', got: {alg_options.get('algorithm', None)}")
            return False
        elif not self.check_options():
            return False
        self.simulation_options = sim_options
        if not self.initialize_traffic_lights():
            return False
        # Initialize Algorithm and population
        alg_options["fitness"] = self.evaluate_population
        self.algorithm: Algorithm = ALGORITHMS[alg_options["algorithm"]](alg_options)
        print(f"Successfully initialize algorithm: '{self.algorithm.name}'")
        if not self.algorithm.init_population(self.cycle_phases, len(self.traffic_lights)):
            return False
        # -------- Main --------
        print(f"Performing: {self.options['generations']} iterations per window: {WINDOW} seconds")
        episodes: int = ceil(
            (self.scenario.config_file.get_end_time() - self.scenario.config_file.get_start_time()) / WINDOW
        )
        print(f"Total episodes: {episodes}")
        total_time: float = 0
        # Perform iterations of algorithm till the end of simulation
        for episode in range(episodes):
            # Iterations over algorithm solutions
            print(f"----------- Episode: {episode + 1}/{episodes} -----------")
            start: float = time.time()
            best: Optional[Population] = None
            for i in range(self.options["generations"]):
                print(f"*** Gen: {i + 1}/{self.options['generations']} ***")
                new: Optional[Union[List[Population], Population]] = self.algorithm.step(i)
                if new is None:
                    raise ValueError(f"Error, solution returned by algorithm: {self.algorithm.name} is invalid!")
                elif isinstance(new, Population):
                    best = new if (best is None or new.is_better(best)) else best
                else:  # list
                    new = sorted(new)
                    best = new[0] if (best is None or new[0].is_better(best)) else best
            end: float = round(time.time() - start, 3)
            print(
                f"Best fitness: {best.fitness} at episode: {episode+1}/{episodes}, "
                f"time taken: {end} seconds."
            )
            total_time += end
            # Save new simulation state
            new_snapshot: str = FilePaths.SCENARIO_SNAPSHOT.format(self.scenario.name, f"{episode}")
            options: dict = self.simulation_options
            if self.snapshot:
                options = deepcopy(self.simulation_options)
                options["--load-state"] = self.snapshot
                options["--begin"] = str(self.current_time)
            evaluate(
                best, self.traffic_lights, self.scenario.config_file.file_path,
                options, self.current_time + WINDOW, new_snapshot
            )
            self.snapshot = new_snapshot
            self.current_time += WINDOW
            # Remove all TLs in snapshot which contain ProgramID = 1 (as that is set by TraCI)
            if not XmlFile.file_exists(self.snapshot):
                return False
            xml_snapshot: XmlFile = XmlFile(self.snapshot)
            for traffic_lights in xml_snapshot.root.findall("tlLogic"):
                if traffic_lights.attrib["programID"] == "1":
                    xml_snapshot.root.remove(traffic_lights)
            xml_snapshot.save()
        # -------- End --------
        # Record phases of TLs into file, save logs
        print(f"{episodes} episodes took in total: {total_time}")
        return self.save_traffic_lights(self.options["tl_file"])

    # -------------------------------- Fitness --------------------------------

    def evaluate_population(self, population: Union[List[Population], Population]) -> bool:
        """
        Evaluates population by continuing the simulation forward, then after calculating
        statistics assigns fitness to the population

        :param population: population to be evaluated
        :return: True on success, false otherwise
        """
        # Initialize options (with state if there is any)
        options: dict = self.simulation_options
        if self.snapshot:
            options = deepcopy(self.simulation_options)
            options["--load-state"] = self.snapshot
            options["--begin"] = str(self.current_time)
        if isinstance(population, Population):
            population = [population]
        start: float = time.time()
        results: List[Tuple[float, int]] = []
        # Parallel evaluation (only when there are multiple populations)
        if self.options["processes"] > 1 and len(population) > 1:
            assert (all(len(pop.pops) == len(self.traffic_lights) for pop in population))
            # print(f"Starting multiprocessing queue with: {self.options['processes']} processes")
            # Safe opening of multi-processing pool
            with multiprocessing.Pool(self.options['processes']) as pool:
                process_results: List[multiprocessing.pool.ApplyResult] = [
                    pool.apply_async(
                        evaluate, args=(
                            chunk, self.traffic_lights, self.scenario.config_file.file_path,
                            options, self.current_time + WINDOW
                        )
                    ) for chunk in self.partition(population, ceil(len(population) / self.options["processes"]))
                ]
                # Close pool
                pool.close()
                pool.join()
                for res in process_results:
                    res = res.get()
                    if isinstance(res, list):
                        results += res
                    else:
                        results.append(res)
        else:  # Sequential
            results = evaluate(
                population, self.traffic_lights, self.scenario.config_file.file_path,
                options, self.current_time + WINDOW
            )
        print(f"Finished evaluating population, took: '{round(time.time() - start, 3)}' seconds.")
        # Assign values to population
        assert(len(results) == len(population) and None not in results)
        for i in range(len(results)):
            # Turn vehicle which left simulation into negative number, as the goal is minimization
            population[i].fitness = (results[i][0], -1*results[i][1])
        return True

    # -------------------------------- Utils --------------------------------

    def save_traffic_lights(self, name: str) -> bool:
        """
        Saves the best found traffic lights phases into additional SUMO file (in the given scenario directory)

        :param name: name of traffic lights files (adds '_tl' suffix after name)
        :return: True on success, false otherwise
        """
        print(f"Saving traffic lights file: {name}_tl")
        file_path: str = FilePaths.SCENARIO_ADDITIONAL.format(self.scenario.name, name + "_tl")
        # As additional file load vehicles template and remove vehicle type
        xml_file: XmlFile = XmlFile(FilePaths.SUMO_VEHICLE_TEMPLATE)
        xml_file.root.remove(xml_file.root.find("vType"))
        for traffic_lights in self.traffic_lights:
            xml_file.root.append(traffic_lights.to_xml())
        return xml_file.save(file_path) and self.check_tl_file(file_path)

    def initialize_traffic_lights(self) -> bool:
        """
        :return: True on success, false otherwise
        """
        print("Initializing traffic lights ...")
        simulation = Simulation(self.scenario.config_file, sim_options).initialize()
        self.current_time = simulation.get_time()
        if simulation is None or not simulation.is_running():
            return False
        # Extract phases from each TL and make copy
        for tl_id in traci.trafficlight.getIDList():
            phases: List[traci.trafficlight.Phase] = deepcopy(list(
                traci.trafficlight.getAllProgramLogics(tl_id)[0].phases
            ))
            if len(phases) == 1:
                print(f"Traffic light: {tl_id} has only 1 phase, ignoring ...")
                continue
            traffic_lights: TrafficLights = TrafficLights(tl_id, phases)
            # Ignore single phase TL
            if len(traffic_lights.green_phases) == 1:
                print(f"Traffic light: {tl_id} has only 1 phase, ignoring ...")
                continue
            self.traffic_lights.append(traffic_lights)
        if len(self.traffic_lights) == 0:
            print("Error, unable to find valid traffic lights!")
            return False
        print(f"Found: {len(self.traffic_lights)} traffic lights to be optimized!")
        simulation.close()
        return True

    def check_options(self) -> bool:
        """
        :return:
        """
        print(f"Checking options passed to TLOptimization: {self.options}")
        if self.options is None or not self.options:
            print("Invalid options given to TrafficLightOptimization Class!")
            return False
        keys: Set[str] = {"processes"}
        if len(keys & self.options.keys()) != len(keys):
            print(f"Error, missing parameters: {keys ^ (keys & self.options.keys())}")
            return False
        # Check processes
        if not isinstance(self.options["processes"], int):
            print(f"Expected parameter processes to be number, got: '{self.options['processes']}'")
            return False
        elif not check_process_count(self.options["processes"]):
            print("Lowering process count to 1 ...")
            self.options["processes"] = 1
        print("All options are correct ...")
        return True

    def check_tl_file(self, file_path: str) -> bool:
        """
        Checks given traffic lights file if the phases are in correct order
        and are defined correctly.

        :param file_path: the given traffic lights file
        :return: True if traffic lights file is correct, false otherwise
        """
        print(f"Checking traffic lights file: {file_path}")
        if not XmlFile.file_exists(file_path):
            return False
        # Initialize traffic lights
        elif not self.traffic_lights:
            if not self.initialize_traffic_lights():
                return False
        tl_file: XmlFile = XmlFile(file_path)
        if not len(tl_file.root.findall("tlLogic")) == len(self.traffic_lights):
            print(f"Traffic lights file does not contain all traffic lights!")
            return False
        mapping: Dict[str, TrafficLights] = {
            tl_object.get_attribute("id"): tl_object for tl_object in self.traffic_lights
        }
        # Check phases and their order for each TL
        for tl_element in tl_file.root.findall("tlLogic"):
            tl_object = mapping[tl_element.attrib["id"]]
            if not tl_object.check_phases(list(tl_element.findall("phase"))):
                return False
        print(f"TL file is correct!")
        return True

    def partition(self, population: List[Population], size: int):
        """
        :param population:
        :param size:
        :return:
        """
        size = max(1, size)
        return (population[i:i+size] for i in range(0, len(population), size))


def make_graph_plots(configs: Dict[str, str], options: dict, end_time: float) -> None:
    """
    Plots average waiting time over the whole simulation for given configuration files

    :param configs: sumo configuration files
    :param options: options of simulation
    :param end_time: end time of simulation
    :return: None
    """
    import matplotlib.pyplot as plt
    # Check existence
    for config in configs.values():
        if not XmlFile.file_exists(config):
            return
    # Extract values
    results: Dict[str, List[float]] = {
        algorithm: sim_log(config, options, end_time) for algorithm, config in configs.items()
    }
    x: np.ndarray = np.arange(25200.5, end_time + 0.5, 0.5)
    # Plot development of average wainting time
    for algorithm, result in results.items():
        plt.plot(x, result, label=f"Algorithm: {algorithm}")
    plt.xlabel("time [sec]")
    plt.ylabel("waiting time [sec]")
    plt.title("Development of waiting time")
    plt.xlim(25200, end_time)
    plt.legend()
    plt.tight_layout()
    plt.savefig("waiting_development.pdf")
    return


if __name__ == '__main__':
    scenario: str = "itsc_25200_26100_red"
    config: str = "itsc_25200_26100_red_act"
    stats: str = FilePaths.SCENARIO_STATISTICS.format(scenario, "sa2")
    alg_options: dict = {
        "algorithm": "SimulatedAnnealing",
        # General parameters
        "selection": "tournament",
        "initialization": "random",
        "population": 10,
        "crossover": "blend",
        "crossover_chance": 0.5,
        "mutation": "gaussian",
        "mutation_chance": 0.15,
        # SimulatedAnnealing parameters
        "temperature": 10000,
        "cooling_rate": 0.01,
        # GeneticAlgorithm parameters
        "elitism": 0.1  # 10% elitism, as the population size is small
    }
    sim_options: dict = {
        "-W": "",  # Ignore warnings
        "--seed": str(SEED),  # Set seed for reproducibility
        "--save-state.rng": "t",
        # f"--tripinfo-output.write-unfinished --duration-log.statistics true --statistic-output": stats  #
    }
    tl_options: dict = {
        "processes": 4,
        "generations": 10,  # Number of times population should be evaluated per each WINDOW timer
        "tl_file": "sa"  # Name of the new TL file to be generated
    }
    configs: Dict[str, str] = {
        "static": FilePaths.SCENARIO_CONFIG.format(scenario, scenario),
        "actuated": FilePaths.SCENARIO_CONFIG.format(scenario, scenario + "_act"),
        "GeneticAlgorithm": FilePaths.SCENARIO_CONFIG.format(scenario, scenario + "_ga"),
        "SimulatedAnnealing": FilePaths.SCENARIO_CONFIG.format(scenario, scenario + "_sa"),
        "NSGA2": FilePaths.SCENARIO_CONFIG.format(scenario, scenario + "_nsga")
    }
    # tlo: TrafficLightOptimization = TrafficLightOptimization(scenario, tl_options)
    # tlo.main(alg_options, sim_options)
    # sim_evaluate(FilePaths.SCENARIO_CONFIG.format(scenario, config), sim_options, 26100)
    make_graph_plots(configs, sim_options, 26100)






