from utc.src.constants.static.file_constants import FilePaths
from typing import Union
from abc import ABC, abstractmethod
from json import load
from jsonschema import validate
from dataclasses import fields


class Options(ABC):
    """
    Class serving as template for classes defining parameters in project,
    provides utility methods (json schemas comparisons).
    """
    @abstractmethod
    def validate_options(self) -> bool:
        """
        :return: True if options are in correct format, validated by JSON schema and other functions.
        """
        raise NotImplementedError("Error, method 'validate_options' must be implemented by children of Options!")

    @staticmethod
    def validate_data(data: dict, schema: Union[dict, str]) -> bool:
        """
        :param data: dictionary to be compared against schema
        :param schema: path to json schema to be used
        :return: True if validation was successful, false otherwise
        """
        print(f"Validating data: {data} with schema: {schema}")
        if isinstance(schema, dict):
            schema_dict: dict = schema
        else:
            with open(FilePaths.JSON_SCHEMA.format(schema), "r") as json_schema:
                schema_dict: dict = load(json_schema)
        if schema_dict is None or not schema_dict:
            raise ValueError(f"Error, invalid schema: '{schema}'")
        return validate(data, schema_dict) is None

    @staticmethod
    def dataclass_from_dict(cls, data):
        """
        Constructs dataclass which contains another dataclasses as parameters from nested
        dictionary, class variable names must correspond to dictionary keys.
        https://stackoverflow.com/questions/53376099/python-dataclass-from-a-nested-dict

        :param cls: data class type
        :param data: nested dictionary
        :return: Data class recursively constructed from given data
        """
        if not isinstance(data, dict):
            return data
        field_types: dict = {var.name: var.type for var in fields(cls)}
        return cls(**{var: Options.dataclass_from_dict(field_types[var], data[var]) for var in data})

    def __post_init__(self) -> None:
        """
        Calls validation against schema if implemented for validity

        :return: None
        """
        assert(self.validate_options())
