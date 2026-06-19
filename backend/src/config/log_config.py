import os
import logging
from datetime import datetime
from typing import Optional
from logging import Logger

from src.config.settings import LOG_DIR, LOG_LEVEL, LOG_TO_FILE


_LOGGING_CONFIGURED = False


def configure_logging(
    log_level: str = LOG_LEVEL,
    log_dir: str = LOG_DIR,
    log_to_file: bool = LOG_TO_FILE,
) -> None:
    global _LOGGING_CONFIGURED

    resolved_level = getattr(logging, str(log_level).upper(), logging.INFO)
    root_logger = logging.getLogger()

    if not _LOGGING_CONFIGURED:
        logging.basicConfig(
            level=resolved_level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            force=True,
        )
        _LOGGING_CONFIGURED = True
    else:
        root_logger.setLevel(resolved_level)

    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(
            log_dir,
            f"backend_{datetime.now().strftime('%Y%m%d')}.log",
        )
        has_file_handler = any(
            isinstance(handler, logging.FileHandler)
            and getattr(handler, "baseFilename", "") == os.path.abspath(log_filename)
            for handler in root_logger.handlers
        )
        if not has_file_handler:
            file_handler = logging.FileHandler(log_filename, encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
            )
            root_logger.addHandler(file_handler)


def setup_logging(
        log_level: str = LOG_LEVEL,
        log_dir: str = LOG_DIR,
        filename: Optional[str] = 'log',
        logToFile: Optional[bool] = LOG_TO_FILE,
        ) -> Logger:

    """
    Set up a standardized logging configuration for the entire project.

    Args:
        log_level (str): Logging level (default: LOG_LEVEL)
        log_dir (str): Directory to store log files (default: 'logs')
        filename (str): Base filename for log files (default: 'log')
        logToFile (bool): Whether to log to file (default: LOG_TO_FILE)
    """
    configure_logging(log_level=log_level, log_dir=log_dir, log_to_file=bool(logToFile))
    logger_name = os.path.splitext(os.path.basename(filename or "log"))[0]
    logger = logging.getLogger(logger_name)

    if logToFile:
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.abspath(
            os.path.join(log_dir, f"{logger_name}_{datetime.now().strftime('%Y%m%d')}.log")
        )
        has_file_handler = any(
            isinstance(handler, logging.FileHandler)
            and getattr(handler, "baseFilename", "") == log_filename
            for handler in logger.handlers
        )
        if not has_file_handler:
            file_handler = logging.FileHandler(log_filename, encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
            )
            logger.addHandler(file_handler)

    return logger
