# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# import sys
# import logging
# from typing import TextIO
# from io import StringIO
import datetime as dt
from pathlib import Path
from dataclasses import dataclass

import yaml

# from astropy.table import Table
from astropy.io import ascii as ioascii
# import nbformat as nbf


@dataclass(order=True)
class FileChange():
    date: dt.date
    author: str
    comment: str = ""


@dataclass
class IRDBFile():
    name: str
    date_created: dt.date
    date_modified: dt.date
    changes: list

    @property
    def last_change(self):
        return max(self.changes)

    @classmethod
    def from_file(cls, file):
        table = ioascii.read(file, format="basic", guess=False)
        comments_str = "\n".join(table.meta["comments"])
        meta = yaml.full_load(comments_str)
        try:
            chgs = list(cls._parse_changes(meta["changes"]))
        except KeyError:
            chgs = None
        return cls(file.name,
                   meta.get("date_created", None),
                   meta.get("date_modified", None),
                   chgs)

    @classmethod
    def from_folder(cls, folder):
        for file in folder.rglob("*.dat"):
            yield cls.from_file(file)

    @staticmethod
    def _parse_changes(changes):
        for change in changes:
            date_str, author, *comments = change.split()
            date = dt.date.fromisoformat(date_str)
            author = author.strip("()")
            comment = " ".join(comments)
            yield FileChange(date, author, comment)

    def validate_dates(self) -> None:
        date_created = self.date_created
        date_modified = self.date_modified

        if self.changes is not None:
            date_last_change = self.last_change.date
            if date_modified is None:
                raise ValueError("Changes listed but no modified date set.")
            if not date_last_change == date_modified:
                msg = f"{date_last_change=!s} not equal to {date_modified=!s}"
                raise ValueError(msg)

        if date_modified is not None:
            if self.changes is None:
                raise ValueError("Modified date set but no changes listed.")
            if date_modified < date_created:
                msg = f"{date_modified=!s} earlier than {date_created=!s}"
                raise ValueError(msg)

if __name__ == "__main__":
    files = list(IRDBFile.from_folder(Path("../")))

    db = {"Data files": {}}
    for f in files:
        try:
            f.validate_dates()
            db["Data files"][f.name] = {"no_conflicts": True}
        except ValueError as err:
            msg = str(err).replace(" ", "_").replace("-", "--")
            db["Data files"][f.name] = {msg: "error"}

    # colnames = ["File", "Last modification"]
    # data = [[f.name for f in files], [f.date_modified for f in files]]
    # tbl = Table(names=colnames, data=data, copy=False)

    # nb = nbf.v4.new_notebook()
    # text = """\
    # # My first automatic Jupyter Notebook
    # This is an auto-generated notebook."""


    # nb["cells"] = [nbf.v4.new_markdown_cell(text),
    #                nbf.v4.new_markdown_cell(tbl.show_in_notebook().data)]
    # fname = "test.ipynb"

    # with open(fname, "w") as f:
    #     nbf.write(nb, f)
