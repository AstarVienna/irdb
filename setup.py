#!/usr/bin/env python3
"""IRDB"""

from distutils.core import setup
import yaml
from .tests.utils import get_packages

# Version number
MAJOR = 0
MINOR = 1
ATTR = 'dev1'

VERSION = '%d.%d%s' % (MAJOR, MINOR, ATTR)


def create_manifest():
    pkgs_dict = get_packages()
    with open("MANIFEST.in", "w") as f:
        for pkg_name in pkgs_dict:
            f.write("include {}/*\n".format(pkg_name))


def setup_package():
    setup(name = 'IRDB',
          version = VERSION,
          description = "Instrument package database",
          author = "Kieran Leschinski",
          author_email = "kieran.leschinski@unive.ac.at",
          url = "http://homepage.univie.ac.at/kieran.leschinski/",
          packages = ["tests"],
          )


if __name__ == '__main__':
    create_manifest()
    setup_package()
