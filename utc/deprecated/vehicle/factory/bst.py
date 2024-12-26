from xml.etree.ElementTree import Element
from utc.src.simulator.vehicle import Vehicle


class BST:
    """ Binary search tree (designed to sort vehicles by time of departure) """

    def __init__(self):
        # Root of BST tree
        self.root: BST.Node = None

    class Node:
        """ Node of binary search tree """

        def __init__(self, vehicle: Vehicle):
            self.l_child = None
            self.r_child = None
            self.vehicle: Vehicle = vehicle

    def binary_insert(self, vehicle: Vehicle) -> None:
        """
        Iteratively inserts vehicle as new node into BST, compares
        others vehicles with their departing time

        :param vehicle: to be inserted
        :return: None
        """
        new_node: BST.Node = BST.Node(vehicle)
        temp_node: BST.Node = self.root
        if temp_node is None:
            self.root = new_node
            return
        temp_pointer: BST.Node = None
        # Find parent node
        while temp_node is not None:
            temp_pointer = temp_node
            if vehicle.get_depart() < temp_node.vehicle.get_depart():
                temp_node = temp_node.l_child
            else:
                temp_node = temp_node.r_child
        # Assign new node to tree
        if temp_pointer is None:
            temp_pointer = new_node
        elif vehicle.get_depart() < temp_pointer.vehicle.get_depart():
            temp_pointer.l_child = new_node
        else:
            temp_pointer.r_child = new_node

    def size(self, node: Node) -> int:
        """
        :param node: starting node from which size will be calculated
        :return: Size of BST
        """
        size = 0
        if node is not None:
            size += 1
            size += self.size(node.l_child)
            size += self.size(node.r_child)
        return size

    def in_order(self, node: Node) -> None:
        """
        Prints vehicles in BST (sorted by lowest departure time to highest)

        :param node: on which traversal should start
        :return: None
        """
        if node is None:
            return
        self.in_order(node.l_child)
        print(node.vehicle)
        self.in_order(node.r_child)

    def sorted_append(self, node: Node, element: Element) -> None:
        """
        Appends vehicles sorted by their departure time to xml element

        :param node: on which appending should start
        :param element: xml element to which vehicles should be appended to
        :return: None
        """
        if node is None:
            return
        self.sorted_append(node.l_child, element)
        element.append(node.vehicle.to_xml())
        self.sorted_append(node.r_child, element)
