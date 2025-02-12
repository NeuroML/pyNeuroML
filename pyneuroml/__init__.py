import logging
import os
import typing

try:
    import importlib.metadata

    __version__ = importlib.metadata.version("pyNeuroML")
except ImportError:
    import importlib_metadata

    __version__ = importlib_metadata.version("pyNeuroML")


JNEUROML_VERSION = "0.14.0"

logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
# do not set level

formatter = logging.Formatter(
    "pyNeuroML >>> %(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
)

ch.setFormatter(formatter)

logger.addHandler(ch)


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
