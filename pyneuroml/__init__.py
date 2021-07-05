import logging

__version__ = '0.5.13'

JNEUROML_VERSION = '0.11.0'

# Define a logger for the package
logging.basicConfig(format="pyNeuroML >>> %(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARN)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('pyNeuroML >>> %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
