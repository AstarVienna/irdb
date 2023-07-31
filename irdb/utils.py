import os
from os import path as pth
from pathlib import Path
import yaml

from irdb.system_dict import SystemDict

PKG_DIR = Path(__file__).parent.parent


def get_packages():
    """
    Returns a dictionary with all packages in the IRDB

    Returns
    -------
    pkgs : dict
        {"packge_name" : "path_to_package"}
    """
    # TODO: update docstring for generator
    for pkg_path in PKG_DIR.iterdir():
        if (pkg_path / f"{pkg_path.name}.yaml").exists():
            yield pkg_path.name, pkg_path

def load_badge_yaml(filename=None):
    """
    Gets the badge yaml file - should be called at the beginning of a test file

    Parameters
    ----------
    filename : str
        Defaults to <IRDB>/_REPORTS/badges.yaml

    Returns
    -------
    badges : SystemDict

    """
    if filename is None:
        filename = "badges.yaml"

    badges = SystemDict()
    with open(pth.join(PKG_DIR, "_REPORTS", filename)) as f:
        badges.update(yaml.full_load(f))

    return badges


def write_badge_yaml(badge_yaml, filename=None):
    """
    Writes the badges yaml dict out to file - should be called during teardown

    Parameters
    ----------
    badge_yaml : SystemDict
        The dictionary of badges.

    filename : str
        Defaults to <IRDB>/_REPORTS/badges.yaml

    """
    if filename is None:
        filename = "badges.yaml"

    if isinstance(badge_yaml, SystemDict):
        badge_yaml = badge_yaml.dic

    with open(pth.join(PKG_DIR, "_REPORTS", filename), "w") as f:
        f.write(yaml.dump(badge_yaml))


def make_badge_report(badge_filename=None, report_filename=None):
    """
    Generates the badges.md file which describes the state of the packages
    """
    if badge_filename is None:
        badge_filename = "badges.yaml"
    if report_filename is None:
        report_filename = "badges.md"

    badge_dict = load_badge_yaml(badge_filename)
    msg = make_entries(badge_dict.dic)

    with open(pth.join(PKG_DIR, "_REPORTS", report_filename), "w") as f:
        f.write(msg)


def make_entries(entry, level=0):
    """
    Recursively generates lines of text from a nested dictionary for badges.md

    Parameters
    ----------
    entry : dict, str, bool, float, int
        A level from a nested dictionary

    level : int
        How far down the rabbit hole we are w.r.t the nested dictionary

    Returns
    -------
    msg : str
        A string for the current entry / dict of entries. To be written to
        badges.md

    """
    special_strings = {"observation" : "blueviolet",
                       "support" : "blue",
                       "missing" : "red",
                       "error" : "red"}

    badge_pattern = "[![](https://img.shields.io/badge/{}-{}-{})]()"
    msg = ""
    if isinstance(entry, dict):
        for key in entry:
            msg += "\n" + "  " * level
            if isinstance(entry[key], dict):
                msg += f"* {key}: " if level else f"## {key}: "
                msg += make_entries(entry[key], level=level+1)
            else:
                if isinstance(entry[key], bool):
                    clr = "green" if entry[key] else "red"

                elif isinstance(entry[key], str):
                    clr = "lightgrey"
                    if entry[key].lower() in special_strings:
                        clr = special_strings[entry[key].lower()]

                elif isinstance(entry[key], (int, float)):
                    clr = "lightblue"
                msg += "* " + badge_pattern.format(key, entry[key], clr)

    return msg


def recursive_filename_search(entry):
    """
    Search through a yaml dict looking for the keyword "filename"

    Parameters
    ----------
    entry : dict
        A yaml nested dictionary

    Returns
    -------
    fnames : list
        List of all filenames found

    """
    fnames = []
    if isinstance(entry, list):
        for item in entry:
            fnames.extend(recursive_filename_search(item))

    if isinstance(entry, dict):
        for key, value in entry.items():
            if key.lower() in {"filename", "file_name"}:
                fnames.append(value)
            elif isinstance(value, (dict, list)):
                fnames.extend(recursive_filename_search(value))

    return fnames
