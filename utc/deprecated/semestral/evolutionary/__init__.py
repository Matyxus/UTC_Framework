from utc.src.semestral.evolutionary.indiv import Individual, Population
from utc.src.semestral.evolutionary.algorithm import Algorithm
from utc.src.semestral.evolutionary.simulated_annealing import SimulatedAnnealing
from utc.src.semestral.evolutionary.genetic_algorithm import GeneticAlgorithm
from utc.src.semestral.evolutionary.nsga2 import NSGA2

ALGORITHMS: dict = {
    "SimulatedAnnealing": SimulatedAnnealing,
    "GeneticAlgorithm": GeneticAlgorithm,
    "nsga": NSGA2
}








