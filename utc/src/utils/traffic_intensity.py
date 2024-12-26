from utc.src.constants.static import FilePaths
from utc.src.constants.file_system import SumoVehiclesFile
from matplotlib import pyplot as plt


class TrafficIntensity:
    """
    Generates image detailing traffic intensity from given vehicle file over its
    duration as avg +- deviation
    """

    def __init__(self, vehicles_file: SumoVehiclesFile):
        """
        :param vehicles_file:
        """
        self.vehicles_file: SumoVehiclesFile = vehicles_file
        assert(self.vehicles_file is not None and self.vehicles_file.is_loaded())

    def generate_image(self, file_path: str, period: float = 300) -> bool:
        """
        :param file_path:
        :param period
        :return:
        """
        print(f"Generating image of traffic intensity to file: '{file_path}'")
        if not self.vehicles_file.has_vehicles():
            print(f"Vehicle file does not contain vehicles!")
            return False
        print(f"Start time: {self.vehicles_file.get_start_time()}, end time: {self.vehicles_file.get_end_time()}")
        print(f"Total number of vehicles: {len(self.vehicles_file.root[1:])}")
        intervals: int = int((self.vehicles_file.get_end_time() - self.vehicles_file.get_start_time()) // period)
        hours: int = int((self.vehicles_file.get_end_time() - self.vehicles_file.get_start_time()) // 3600)
        print(f"Total number of hours in scenario: {intervals}, period: {period}")
        # Data
        x: list = []
        y: list = []
        for i in range(intervals):
            y.append(len(self.vehicles_file.get_vehicles((i * period, (i+1)*period))))
            x.append(i*period)
        average: float = sum(y) / len(y)  # average amount of vehicles per period
        deviation: float = (sum([(i - average) ** 2 for i in x]) / len(y)) ** (1/2)
        # Plot
        plt.xlim((0, max(x)))
        plt.ylim((0, max(y)+1000))
        plt.plot(x, y)
        print(f"Average: {average}, deviation: {deviation}")
        plt.plot(x, [average] * len(x), label='Mean', linestyle='--', color="red")
        plt.xticks([i*3600 for i in range(hours+1)], labels=[i for i in range(hours+1)])
        plt.yticks([i*1000 for i in range((max(y) // 1000)+2)])
        plt.xlabel("Time [hours]")
        plt.ylabel("Vehicles [thousands]")
        plt.title("Traffic intensity")
        plt.tight_layout()
        plt.show()
        return True


# For testing purposes
if __name__ == '__main__':
    scenario_name: str = "itsc"
    temp: TrafficIntensity = TrafficIntensity(SumoVehiclesFile(FilePaths.SCENARIO_VEHICLES.format(scenario_name, scenario_name)))
    temp.generate_image("", period=1800)
