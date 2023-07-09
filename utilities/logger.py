import logging
import os


LOG_DIR = f"{os.pardir}{os.sep}logs{os.sep}"


def create_logger(log_file):
    """user responsible for file extension"""
    if not os.path.isdir(LOG_DIR):
        os.mkdir(LOG_DIR)

    format = "%(levelname)s:\t%(asctime)s\n\t%(message)s"
    formatter = logging.Formatter(format)

    error_file = f"{LOG_DIR}{log_file}.log"
    error_file_handler = logging.FileHandler(error_file)
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)

    logger = logging.getLogger(__name__)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(error_file_handler)
    logger.setLevel(logging.ERROR)

    return logger


def reset_logger(log_file):
    existing_log_file = f"{LOG_DIR}{log_file}.log"
    if os.path.isfile(existing_log_file):
        os.remove(existing_log_file)
