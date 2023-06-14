import os
from os import path as pth
from datetime import datetime as dt

import pytest

from .. import publish as pub


@pytest.fixture(name="preserve_versions", scope="function")
def fixture_preserve_versions():
    """Preserve the versions of test packages."""
    p_test_package = pub.PKGS_DIR / "test_package" / "version.yaml"

    # Backup version information.
    b_yaml_packages = pub.PATH_PACKAGES_YAML.read_bytes()
    b_yaml_test_package = p_test_package.read_bytes()

    # yield instead of return so the fixture can clean up afterwards
    yield

    # Put the original values back.
    pub.PATH_PACKAGES_YAML.write_bytes(b_yaml_packages)
    p_test_package.write_bytes(b_yaml_test_package)


def test_make_packages(preserve_versions):
    os.chdir(pth.join(pth.dirname(__file__), "../../"))
    pkg_name = "test_package"
    now = str(dt.now())[:10]
    zip_name = pub.make_package(pkg_name, release="dev")

    assert zip_name == f"{pkg_name}.{now}.dev"
    assert pth.exists(pth.join("_ZIPPED_PACKAGES", zip_name+".zip"))


def test_run_main(preserve_versions):
    argv = ["", "-c", "test_package", "-p", "<insert_if_running_locally"]
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
