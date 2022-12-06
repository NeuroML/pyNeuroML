import logging

__version__ = "0.7.5"

JNEUROML_VERSION = "0.12.1"

# Define a logger for the package
logging.basicConfig(
    format="pyNeuroML >>> %(levelname)s - %(message)s",
    level=logging.WARN,
)


def print_v(msg):
    """Print message to console.

    This is to be used for printing out messages during ordinary usage of the
    tool. For status monitoring, fault investigation etc., use the logger.

    :param msg: string to print
    :type msg: str
    """
    print("pyNeuroML >>> " + msg)
