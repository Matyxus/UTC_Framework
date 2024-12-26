from typing import Dict, List, Set, Any, TypeVar, Optional
from inspect import Parameter


class ArgumentConverter:
    """
    Class converting arguments from one type to another,
    provides static methods
    """
    allowed_bool_values: Set[str] = {"t", "true", "f", "False"}
    recognized_values: Dict[str, Any] = {
        "None": None,
        "True": True,
        "False": False
    }

    @staticmethod
    def to_dict() -> Dict[str, str]:
        pass

    @staticmethod
    def to_str() -> str:
        pass





