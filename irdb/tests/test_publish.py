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


# def rename_zips():
#     from datetime import datetime as dt
#     from glob import glob
#     import os
#
#     os.chdir("F:/Work/irdb/_OLD_FILES")
#     for fname in glob("*.zip"):
#         base = fname.split(".")[0]
#         mod_date = str(dt.fromtimestamp(os.path.getmtime(fname)))[:10]
#         new_name = f"{base}.{mod_date}.zip"
#         print(fname, new_name)
#         os.rename(fname, new_name)
