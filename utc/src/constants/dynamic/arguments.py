import argparse


def get_args() -> dict:
    """
    :return: Arguments passed to command line
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Argument parser for UTC project.")
    # --------------------- Logging ---------------------
    parser.add_argument(
        "-c", "--config", dest="config", type=str,
        default="", help="Set the configuration file."
    )
    # Export dictionary with arguments
    return vars(parser.parse_args())
