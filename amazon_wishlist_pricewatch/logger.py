"""TODO"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Create handlers.
console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(
    Path(Path(__file__).parent.absolute(), "pricewatch.log"),
    mode="a+",
    maxBytes=2 * 1024 * 1024,  # 2MB max log size.
    backupCount=5,  # Keep max 5 historical logs.
)
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)

# Create formatters and add to handlers.
console_format = logging.Formatter("%(levelname)s - %(message)s")
file_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_format)
file_handler.setFormatter(file_format)

# Add handlers to logger.
logger.addHandler(console_handler)
logger.addHandler(file_handler)
