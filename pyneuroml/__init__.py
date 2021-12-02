import logging

__version__ = "0.5.18"

JNEUROML_VERSION = "0.11.0"

# Define a logger for the package
logging.basicConfig(
    format="pyNeuroML >>> %(levelname)s - %(message)s",
    level=logging.WARN,
)
