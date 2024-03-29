import logging

# Get the logger for the current package
_LOGGER = logging.getLogger("matbii")

# Set logger level to DEBUG
_LOGGER.setLevel(logging.DEBUG)

# Create a stream handler and set its level to DEBUG
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# Configure formatter
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Add handler to the logger
_LOGGER.addHandler(handler)
