#!/usr/bin/env python3
"""IRDB"""

from distutils.core import setup
import os
import glob
import yaml

# Version number
MAJOR = 0
MINOR = 1
ATTR = 'dev1'

VERSION = '%d.%d%s' % (MAJOR, MINOR, ATTR)


def create_manifest():
    with open("packages.yaml") as f:
        PKGS = yaml.load(f)

        with open("MANIFEST.in", "w") as f:
            for pkg_name in PKGS:
                f.write("include {}/*\n".format(PKGS[pkg_name]["dir"]))


def setup_package():
    setup(name = 'IRDB',
          version = VERSION,
          description = "Instrument package database",
          author = "Kieran Leschinski",
          author_email = "kieran.leschinski@unive.ac.at",
          url = "http://homepage.univie.ac.at/kieran.leschinski/",
          )


if __name__ == '__main__':
    create_manifest()
    setup_package()
