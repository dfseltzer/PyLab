"""
Helper functions to tie it all together
"""

import json
import os
import pathlib
import logging

DATA_REL_PATH = r"data"
DATA_ABS_PATH = None

if DATA_ABS_PATH is None:
    fpath, fname = os.path.split(__file__)
    DATA_ABS_PATH = pathlib.Path(fpath, DATA_REL_PATH)

def load_data_file(fname):
    """
    Load a data file from the data directory.

    :param fname: filename to load. not including suffix or path.
    :return: data loaded from file as dict
    """

    base_path = pathlib.Path(DATA_ABS_PATH, fname)  # type: ignore
    candidates = (base_path, pathlib.Path(f"{base_path}.json"))

    full_path = next((path for path in candidates if path.is_file()), None)
    if full_path is None:
        raise FileNotFoundError(f"Data file '{fname}' not found in {DATA_ABS_PATH}")

    with open(full_path, "r") as fobj:
        fdat = json.load(fobj)

    return fdat

def update_data_file(fname, data):
    """
    Update a data file in the data directory.

    :param fname: filename to update. not including suffix or path.
    :param data: data to write.  For json, this should be a dictionary object.
    """
    base_path = pathlib.Path(DATA_ABS_PATH, fname)  # type: ignore
    candidates = (base_path, pathlib.Path(f"{base_path}.json"))

    full_path = next((path for path in candidates if path.is_file()), None)
    if full_path is None:
        raise FileNotFoundError(f"Data file '{fname}' not found in {DATA_ABS_PATH}")
    
    with open(full_path, "w") as fobj:
        json.dump(data, fobj, indent=4, sort_keys=True)
    

def list_data_files(glob="*"):
    """
    List data files, matching a given glob if one is provided.

    :param glob: Description
    """
    base_path = pathlib.Path(DATA_ABS_PATH)  # type: ignore
    return list(fp.name for fp in base_path.glob(glob))


class CustomFormatter(logging.Formatter):
    """
    Thanks https://stackoverflow.com/users/9150146/sergey-pleshakov
    https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    Modified just a smidge.
    """
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(message)s"    #type: ignore

    FORMATS = {
        logging.DEBUG: grey + format + reset,               #type: ignore
        logging.INFO: green + format + reset,               #type: ignore
        logging.WARNING: yellow + format + reset,           #type: ignore
        logging.ERROR: red + format + reset,                #type: ignore
        logging.CRITICAL: bold_red + format + reset         #type: ignore
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

