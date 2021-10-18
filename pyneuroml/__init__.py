import logging

__version__ = "0.5.18"

JNEUROML_VERSION = "0.11.0"

# Define a logger for the package
logging.basicConfig(
    format="pyNeuroML >>> %(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARN,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("pyNeuroML >>> %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
