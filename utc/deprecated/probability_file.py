from utc.src.constants.file_system.my_file import MyFile
from utc.src.constants.static import FileExtension, FilePaths
from typing import Dict, List, Union, Optional


class ProbabilityFile(MyFile):
    """
    Class representing files containing probabilities
    of vehicle flows existing between junctions
    """

    def __init__(self, file_path: str, mode: str = "w+"):
        super().__init__(file_path, mode, FileExtension.PROB)
        self.probability_matrix: Dict[str, Dict[str, int]] = {
            # from_junction : {to junction : probability}, ...
        }

    def add_junction(self, junction_id: Union[int, str]) -> bool:
        """
        :param junction_id:
        :return: True on success, false otherwise
        """
        if self.junction_exists(junction_id):
            print(f"Junction: '{junction_id}' is already recorded!")
            return False
        self.probability_matrix[str(junction_id)] = {}
        return True

    def add_probability(self, from_junction: Union[int, str], to_junction: Union[int, str], probability: int) -> None:
        """
        :param from_junction: starting junction of flow
        :param to_junction: final junction of flow
        :param probability: of flow existing between junctions (the higher the number,
        higher the chance)
        :return: None
        """
        if not self.junction_exists(from_junction):
            self.add_junction(from_junction)
        elif str(to_junction) in self.probability_matrix[from_junction]:
            print(f"Mapping of junctions: {from_junction} -> {to_junction} already exists!")
            return
        elif probability < 0:
            print(f"Probability cannot be lower than '0', got: '{probability}'")
            return
        self.probability_matrix[str(from_junction)][str(to_junction)] = probability

    def junction_exists(self, junction_id: Union[int, str]) -> bool:
        """
        :param junction_id:
        :return:
        """
        return str(junction_id) in self.probability_matrix

    def read_file(self) -> Optional[Dict[str, Dict[str, int]]]:
        """
        :return: Probability matrix read from file, None if error occurred
        """
        lines: List[str] = []
        # Read file
        self.mode = "r+"
        with self as probability_file:
            if probability_file is None:
                print(f"File '{self.file_path}' does not exist!")
                self.mode = "w+"
                return None
            lines = probability_file.read().splitlines()
        self.mode = "w+"
        # Process file
        if not lines:
            print(f"File '{self.file_path}' is empty!")
            return None
        # Expecting first line to be starting junction ids
        in_junctions: List[str] = lines.pop(0).split()
        if not in_junctions:
            print(f"No starting junctions found on first line, got: {in_junctions} !")
            return None
        self.probability_matrix.clear()
        for line in lines:
            probabilities: List[str] = line.split()
            to_junction: str = probabilities.pop(0)
            if len(probabilities) != len(in_junctions):
                print(
                    f"Number of probabilities does not match number of starting"
                    f"junctions, expected: {len(in_junctions)}, got: {len(probabilities)}"
                )
                return None
            for from_junction, probability in zip(in_junctions, probabilities):
                try:
                    self.add_probability(from_junction, to_junction, int(probability))
                except ValueError as e:
                    print(f"Error: {e}, probability must be number, got: {probability}")
                    return None
        return self.probability_matrix

    def save(self, file_path: str = "default") -> bool:
        if file_path != "default":
            self.file_path = file_path
        if not self.file_path.endswith(self.extension):
            print(
                f"For Info file expected extension to be: '{self.extension}'"
                f", got: '{file_path}' !"
            )
            return False
        # Save file
        with self as probability_file:
            if probability_file is None:
                return False
            # 1st row of matrix (junction ids)
            junctions: List[str] = sorted(list(self.probability_matrix.keys()))
            probability_file.write("  " + " ".join(junctions))
            for junction_id in junctions:
                # Assert that junction to junction mapping has probability of 0
                if self.probability_matrix[junction_id].get(junction_id, None) is not None:
                    print(
                        f"Expecting probability of same junctions: '{junction_id}' -> '{junction_id}'"
                        f" to be '0', got: '{self.probability_matrix[junction_id][junction_id]}'"
                    )
                    return False
                probabilities: List[str] = [
                    # For missing probabilities write 0
                    self.probability_matrix[junction_id][j] if self.junction_exists(j) else "0" for j in junctions
                ]
                probability_file.write(junction_id + " " + " ".join(probabilities))
        print(f"Successfully saved '.info' file: '{self.file_path}'")
        return True

    def get_known_path(self, file_name: str) -> str:
        # Probability files for networks
        if self.file_exists(FilePaths.MAP_PROB.format(file_name), message=False):
            return FilePaths.MAP_PROB.format(file_name)
        return file_name  # No default path
