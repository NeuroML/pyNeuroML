import logging
import os
import typing

try:
    import importlib.metadata

    __version__ = importlib.metadata.version("pyNeuroML")
except ImportError:
    import importlib_metadata

    __version__ = importlib_metadata.version("pyNeuroML")


JNEUROML_VERSION = "0.13.1"

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


# read from env variable if found
try:
    java_max_memory = os.environ["JNML_MAX_MEMORY_LOCAL"]
except KeyError:
    java_max_memory = "400M"

DEFAULTS: typing.Dict[str, typing.Any] = {
    "v": False,
    "default_java_max_memory": java_max_memory,
    "nogui": False,
}
