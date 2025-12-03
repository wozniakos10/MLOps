import logging
import os


def get_configured_logger(name: str = "lab01-homework-logger", log_file: str | None = None, level: int = logging.INFO) -> logging.Logger:
    """Creating logger instance"""
    # Creating logger with the specified name and level
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Checking if the logger already has handlers defined
    if not logger.hasHandlers():
        # Log formatting settings
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Creating console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # If log_file is provided, add file handler
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)  # Creating directories if not exist
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
