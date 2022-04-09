import os
from os import path as pth
from datetime import datetime as dt

from .. import publish as pub


def test_make_packages():
    os.chdir(pth.join(pth.dirname(__file__), "../../"))
    pkg_name = "test_package"
    now = str(dt.now())[:10]
    zip_name = pub.make_package(pkg_name, release="dev")

    assert zip_name == f"{pkg_name}_{now}_dev"
    assert pth.exists(pth.join("_ZIPPED_PACKAGES", zip_name+".zip"))


def run_main():
    argv = ["", "-c", "-u", "test_package", "-p", "<insert_if_running_locally"]
    pub.main(argv)
