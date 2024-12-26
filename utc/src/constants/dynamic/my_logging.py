from utc.src.constants.static.file_constants import FilePaths
from utc.src.constants.static.colors import TerminalColors
from utc.src.constants.options.logging_options import LoggingOptions
from typing import Optional
import logging
from sys import stdout
from typing import Dict
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """
    Class handling colored output of logging module.
    """
    def __init__(self, pattern: str):
        """
        :param pattern: Formatted string for printing
        """
        super().__init__(pattern)
        self.color_map: Dict[str, str] = {
            # Log level : color
            'DEBUG': TerminalColors.WHITE,
            'INFO': TerminalColors.BRIGHT_WHITE,
            'WARNING': TerminalColors.YELLOW,
            'ERROR': TerminalColors.RED,
            'CRITICAL': TerminalColors.BRIGHT_RED,
        }

    def format(self, record: logging.LogRecord) -> str:
        """
        :param record: of logging
        :return: Formatted string of log record
        """
        level_name: str = record.levelname
        # Check if user wants colors in logs (only in printed version, log file does not contain them)
        color: str = self.color_map.get(level_name, TerminalColors.WHITE)  # default white
        record.levelname = '{0}{1}{2}'.format(color, level_name, TerminalColors.END_SEQ)
        return logging.Formatter.format(self, record)


def initialize_logger(options: Optional[LoggingOptions] = None) -> logging.Logger:
    """
    https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output - response by KCJ

    :param options: parameters of logging (optional)
    :return: Root logger
    """
    options = (options if options is not None else LoggingOptions())
    # Create top level (root) logger
    logger: logging.Logger = logging.getLogger("root")
    logger.handlers.clear()
    # Add console handler using custom ColoredFormatter
    ch = logging.StreamHandler(stdout)
    ch.setLevel(options.level)
    if options.colored:
        ch.setFormatter(ColoredFormatter("[%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"))
    else:
        ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"))
    logger.addHandler(ch)
    # Add file handler, if enabled
    if options.file:
        file_name: str = (
            FilePaths.LOG_FILE.format(datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            if options.file == "default" else options.file
        )
        fh = logging.FileHandler(file_name)
        fh.setLevel(options.level)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    # Set log level
    logger.setLevel(options.level)
    # Show msg about loaded config
    logger.info(f"Initializing logger: '{logger.name}' with options: {options}")
    return logger
