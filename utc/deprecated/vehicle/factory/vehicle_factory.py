from utc.src.simulator.vehicle.generators import VehicleGenerator, VehicleFlows, VehicleTrips
from utc.src.simulator.vehicle.factory.bst import BST
from utc.src.graph import Graph
from xml.etree.ElementTree import Element
from typing import Dict, List, Tuple


class VehicleFactory(VehicleGenerator):
    """
    Class holding all vehicle generators and
    providing the method to sort vehicles (by time of departure)
    and saving them into xml_element
    """

    def __init__(self, graph: Graph):
        super().__init__(graph)
        print("Initialized VehicleFactory")
        # Vehicle generators
        self.vehicle_flows: VehicleFlows = VehicleFlows()
        self.vehicle_trips: VehicleTrips = VehicleTrips()
        # Merge
        self.merge(self.vehicle_flows)
        self.merge(self.vehicle_trips)

    def save(self, root: Element) -> None:
        """
        Appends routes, vehicles from created generators to BST for sorting,
        afterwards to given root of xml file

        :param root: of '.rou.xml' file
        :return: None
        """
        if root is None:
            print(f"Cannot add vehicles to root of type 'None' !")
            return
        # Generate vehicles and sort them in BST
        print(f"Sorting vehicles by depart time using BinarySearchTree...")
        vehicles_bst: BST = BST()
        for generator in self.generators:
            for vehicle in generator:
                vehicles_bst.binary_insert(vehicle)
        # Add routes before vehicle!
        for route in self.routes:
            root.append(route.to_xml())
        # Add vehicles to xml root
        vehicles_bst.sorted_append(vehicles_bst.root, root)
        print(f"Added: {len(root.findall('vehicle'))} vehicles")

    # -------------------------------------------- Utils --------------------------------------------

    def get_methods(self) -> List[Tuple['VehicleGenerator', Dict[str, callable]]]:
        return self.vehicle_flows.get_methods() + self.vehicle_trips.get_methods()
