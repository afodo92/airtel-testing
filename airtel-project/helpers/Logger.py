from __future__ import annotations
import os
import logging
from logging import handlers


def create_logger(name: str, log_level: str, log_path: str, log_file: str, reset_log: bool = False, max_log_bytes=1000000, max_log_backups=10) -> logging.getLogger() or None:
    """
    Create a logger object. Script logs will be sent to console (INFO level) and a log file. ApiSession logs will be
    sent to a separate file only.
    :param name: the name of the current module
    :param log_level: the log level for this logger object
    :param log_path: path to the log file
    :param log_file: the log file name
    :param reset_log: True means open with w, False meanse open with a
    :return: the logger object
    """
    log = None
    file_mode = 'w' if reset_log else 'a'
    try:
        log = logging.getLogger(name)
        if log_level == "CRITICAL":
            log.setLevel(logging.CRITICAL)
        elif log_level == "ERROR":
            log.setLevel(logging.ERROR)
        elif log_level == "WARNING":
            log.setLevel(logging.WARNING)
        elif log_level == "INFO":
            log.setLevel(logging.INFO)
        elif log_level == "DEBUG":
            log.setLevel(logging.DEBUG)
        else:
            # INFO is the default log level, if a specific level is not specified
            log.setLevel(logging.INFO)
        format_str = '%(asctime)s\t%(levelname)s -- %(processName)s %(filename)s:%(lineno)s -- %(message)s'
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(format_str))
        console_handler.setLevel(logging.INFO)  # only display warning level logs in the console
        create_folder(log_path)
        file = create_file(log_path, log_file)
        #file_handler = logging.FileHandler(file, 'w')
        file_handler = handlers.RotatingFileHandler(filename=file, mode=file_mode, maxBytes=max_log_bytes, backupCount=max_log_backups)
        file_handler.setFormatter(logging.Formatter(format_str))

        log.addHandler(console_handler)
        log.addHandler(file_handler)
    except Exception as detailed_exception:
        print(f"Exception occurred while attempting to create logger named: {name}\n<{detailed_exception}>")
    return log


def create_file(*args: str) -> str or None:
    """
    Creates a file if it doesn't already exist.
    :param args: the string elements that comprise the path of the file and its name and extension.
    :return: the file path
    """
    file = os.path.join(*args)
    if not os.path.exists(file):
        try:
            open(file, 'x').close()
        except Exception as detailed_exception:
            print(f"Exception occurred while attempting to create file: {file}\n<{detailed_exception}>")
            return None
    return file


def create_folder(*args: str) -> str or None:
    """
    Creates a folder if it doesn't already exist.
    :param args: the string elements that comprise the path of the folder and its name
    :return: the folder path
    """
    folder = os.path.join(*args)
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except Exception as detailed_exception:
            print(f"Exception occurred while attempting to create folder: {folder}\n<{detailed_exception}>")
            return None
    return folder
