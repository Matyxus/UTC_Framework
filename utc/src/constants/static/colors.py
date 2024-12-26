class TerminalColors:
    """
    Class containing constant variables for default
    colors of logging prints to terminal.
    https://en.wikipedia.org/wiki/ANSI_escape_code
    """
    WHITE: str = '\033[37m'
    BRIGHT_WHITE: str = '\033[97m'
    YELLOW: str = '\033[33m'
    RED: str = '\033[31m'
    BRIGHT_RED: str = '\033[91m'
    # Utils
    END_SEQ: str = '\033[0m'  # Escape sequence


class GraphColors:
    """
    Class containing constant variables for default colors of graph objects.
    """
    BACKGROUND: str = "#111111"  # Dark (close to being black)
    EDGE_COLOR: str = "#999999"  # grey
    JUNCTION_COLOR: str = "white"
    ROUTE_COLOR: str = "blue"
    # Fringe junctions
    JUNCTION_START_COLOR: str = "green"
    JUNCTION_END_COLOR: str = "blue"
    JUNCTION_START_END_COLOR: str = "#FFD632"
