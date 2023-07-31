#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module/script Description.

Created on Fri Jul 28 15:42:59 2023

@author: ghost
"""

import logging
from warnings import warn
from pathlib import Path
from typing import TextIO
# from io import StringIO
from numbers import Number
from string import Template
from collections.abc import Mapping

import yaml

from irdb.system_dict import SystemDict


PKG_DIR = Path(__file__).parent.parent


def _fix_badge_str(badge_str: str) -> str:
    """Eliminate any spaces and single dashes in badge string."""
    return badge_str.replace(" ", "_").replace("-", "--")


class Badge():
    pattern = Template("[![](https://img.shields.io/badge/$key-$val-$col)]()")
    colour = "lightgrey"

    def __new__(cls, key: str, value):
        if isinstance(value, bool):
            return super().__new__(BoolBadge)
        if isinstance(value, Number):
            return super().__new__(NumBadge)
        if isinstance(value, str):
            if value.startswith("!"):
                return super().__new__(MsgOnlyBadge)
            return super().__new__(StrBadge)
        raise TypeError(value)

    def __init__(self, key: str, value):
        self.key = _fix_badge_str(key)
        self.value = _fix_badge_str(value)

    def write(self, stream: TextIO) -> None:
        """Write formatted pattern to I/O stream"""
        stream.write("* ")
        _dict = {"key": self.key, "val": self.value, "col": self.colour}
        stream.write(self.pattern.substitute(_dict))


class BoolBadge(Badge):
    colour = "red"
    def __init__(self, key: str, value: bool):
        super().__init__(key, value)
        if self.value:
            self.colour = "green"


class NumBadge(Badge):
    colour = "lightblue"


class StrBadge(Badge):
    special_strings = {
        "observation" : "blueviolet",
        "support" : "deepskyblue",
        "error" : "red",
        "missing" : "red",
        "warning" : "orange",
        "conflict" : "orange",
        "incomplete" : "orange",
        "ok": "green",
        "found": "green",
        "not found": "red",
        }

    def __init__(self, key: str, value: str):
        super().__init__(key, value)
        self.colour = self.special_strings.get(self.value.lower(), "lightgrey")


class MsgOnlyBadge(StrBadge):
    pattern = Template("[![](https://img.shields.io/badge/$key-$col)]()")

    def __init__(self, key: str, value: str):
        # value = value.removeprefix("!")
        # TODO: for Python 3.8 support:
        value = value[1:]
        super().__init__(key, value)


class BadgeReport(SystemDict):
    def __init__(self, filename=None):
        print("\nREPORT INIT")
        self.filename = filename or "badges.yaml"
        self.path = Path(PKG_DIR, "_REPORTS", self.filename)
        super().__init__()

    def __enter__(self):
        print("\nREPORT ENTER")
        try:
            with self.path.open(encoding="utf-8") as file:
                self.update(yaml.full_load(file))
        except FileNotFoundError:
            logging.warning("%s not found, init empty dict", self.path)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        print("\nREPORT EXIT")
        self.write_yaml()

    def write_yaml(self):
        dumpstr = yaml.dump(self.dic, sort_keys=False)
        self.path.write_text(dumpstr, encoding="utf-8")


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
    warn(("Using this function directly is deprecated, use BadgeReport "
          "context manager instead."), DeprecationWarning, stacklevel=2)
    if filename is None:
        filename = "badges.yaml"

    badges = SystemDict()

    try:
        with Path(PKG_DIR, "_REPORTS", filename).open(encoding="utf-8") as file:
            badges.update(yaml.full_load(file))
    except FileNotFoundError:
        logging.warning("%s not found, init empty dict", filename)

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
    warn(("Using this function directly is deprecated, use BadgeReport "
          "context manager instead."), DeprecationWarning, stacklevel=2)
    if filename is None:
        filename = "badges.yaml"

    if isinstance(badge_yaml, SystemDict):
        badge_yaml = badge_yaml.dic

    path = Path(PKG_DIR, "_REPORTS", filename)
    path.write_text(yaml.dump(badge_yaml), encoding="utf-8")


def make_badge_report(badge_filename=None, report_filename=None):
    """
    Generates the badges.md file which describes the state of the packages
    """
    if badge_filename is None:
        badge_filename = "badges.yaml"
    if report_filename is None:
        report_filename = "badges.md"

    badge_dict = load_badge_yaml(badge_filename)

    path = Path(PKG_DIR, "_REPORTS", report_filename)
    with path.open("w", encoding="utf-8") as file:
        make_entries(file, badge_dict.dic)


def make_entries(stream: TextIO, entry, level=0) -> None:
    """
    Recursively write lines of text from a nested dictionary to text stream.

    Parameters
    ----------
    stream : TextIO
        I/O stream to write the badges to.

    entry : dict, str, bool, float, int
        A level from a nested dictionary

    level : int
        How far down the rabbit hole we are w.r.t the nested dictionary

    Returns
    -------
    None
    """
    if not isinstance(entry, Mapping):
        return

    for key, value in entry.items():
        stream.write("\n")
        stream.write("  " * level)
        if isinstance(value, Mapping):
            stream.write(f"* {key}: " if level else f"## {key}: ")
            # recursive
            make_entries(stream, value, level=level+1)
        else:
            Badge(key, value).write(stream)


if __name__ == "__main__":
    make_badge_report()
