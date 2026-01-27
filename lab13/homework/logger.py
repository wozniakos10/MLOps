import logging
import os


def get_configured_logger(
    name: str = "lab01-homework-logger",
    log_file: str | None = None,
    level: int = logging.DEBUG,
    log_to_console: bool = True,
) -> logging.Logger:
    """Creating logger instance

    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level (default INFO)
        log_to_console: If True, logs are printed to terminal (default True)
    """
    # Creating logger with the specified name and level
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent propagation to root logger (stops duplicate console output)
    logger.propagate = False

    # Checking if the logger already has handlers defined
    if not logger.hasHandlers():
        # Log formatting settings
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Creating console handler if log_to_console is True
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # If log_file is provided, add file handler
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir:  # Only create directories if there's a directory path
                os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    # If not logging to console, also silence root logger and other loggers
    if not log_to_console:
        logging.getLogger().setLevel(logging.WARNING)
        logging.getLogger().handlers = []
        # Silence common noisy loggers
        for noisy_logger in [
            "opentelemetry",
            "guardrails",
            "httpx",
            "httpcore",
            "urllib3",
        ]:
            logging.getLogger(noisy_logger).setLevel(logging.ERROR)
        # Suppress Python warnings
        import warnings

        warnings.filterwarnings("ignore")

    return logger
