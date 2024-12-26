from typing import Dict, List
from copy import deepcopy


class PddlStruct:
    """
    Class holding attributes of '.pddl' problem files in data structures,
    only general ones such as ':object', ':init', ':goal', others
    such as ':domain', 'problem' are defined in PddlProblem Class.
    """
    def __init__(self):
        self.object: Dict[str, List[str]] = {
            # group_name: [object_id1, ....]
        }
        self.init: List[str] = []  # List of initial states
        self.goal: List[str] = []  # List of goal states

    # ------------------------------------ Adders ------------------------------------

    def add_object(self, group_name: str, object_id: str) -> bool:
        """
        :param group_name: name of object's group
        :param object_id: id of object
        :return: True on success, false otherwise
        """
        if not group_name:
            print(f"Invalid group name: {group_name}")
            return False
        elif not object_id:
            print(f"Invalid id of object: {object_id}!")
            return False
        # Add if missing
        if group_name not in self.object:
            self.object[group_name] = []
        self.object[group_name].append(object_id)
        return True

    def add_init_state(self, init_state: str) -> None:
        """
        :param init_state: to be added into ':init' (non-empty and must start and end with parentheses)
        :return: None
        """
        if not init_state or not init_state.startswith("(") or not init_state.endswith(")"):
            print(f"Invalid state added to ':init': {init_state}")
            return
        self.init.append(init_state)

    def add_goal_state(self, goal_state: str) -> None:
        """
        :param goal_state: to be added into ':goal' (non-empty and must start and end with parentheses)
        :return:
        """
        if not goal_state or not goal_state.startswith("(") or not goal_state.endswith(")"):
            print(f"Invalid state added to ':goal': {goal_state}")
            return
        self.goal.append(goal_state)

    # ------------------------------------ Utils ------------------------------------

    def object_to_string(self) -> str:
        """
        :return: pddl representation of ':objects' as string (with new line)
        """
        ret_val: str = "(:objects\n"
        for object_group, objects in self.object.items():
            ret_val += (" ".join(objects) + f" - {object_group}\n")
        return ret_val + ")\n"

    def init_to_str(self) -> str:
        """
        :return:  pddl representation of ':init' as string (with new line)
        """
        ret_val: str = "(:init\n"
        for init_state in self.init:
            ret_val += (init_state + "\n")
        return ret_val + ")\n"

    def goal_to_str(self) -> str:
        """
        :return: pddl representation of ':goal' as string (with new line)
        """
        ret_val: str = "(:goal (and\n"
        for goal_state in self.goal:
            ret_val += (goal_state + "\n")
        return ret_val + "))\n"

    def clear(self) -> None:
        """
        Clears all data structures

        :return: None
        """
        self.object.clear()
        self.init.clear()
        self.goal.clear()

    # ------------------------------------ Magic Methods ------------------------------------

    def __str__(self) -> str:
        """
        :return: string representation of ':objects', ':init', ':goal' (ending with new line)
        """
        return self.object_to_string() + self.init_to_str() + self.goal_to_str()

    def __or__(self, other: 'PddlStruct') -> 'PddlStruct':
        """
        Merges two PddlStruct together, (result is saved in new PddlStruct).

        :param other: PddlStruct
        :return: new PddlStruct
        :raises: AttributeError if parameter 'other' is not PddlStruct Class
        """
        if isinstance(other, PddlStruct):
            tmp: PddlStruct = deepcopy(self)
            # Merge ':object'
            for key, value in other.object.items():
                # If key exists, it is expected, it already is in self.object
                if key not in tmp.object:
                    tmp.object[key] = deepcopy(value)
            # Merge ':init' (it is assumed, items in other.init are not in self.init)
            tmp.init.extend(other.init)
            # Merge ':goal' (it is assumed, items in other.goal are not in self.goal)
            tmp.goal.extend(other.goal)
            return tmp
        else:
            raise AttributeError("Cannot merge PddlStruct class with any other class!")

    def __ror__(self, other: 'PddlStruct') -> 'PddlStruct':
        """
        :param other: PddlStruct
        :return: new PddlStruct
        :raises: AttributeError if parameter 'other' is not PddlStruct Class
        """
        return self.__or__(other)
