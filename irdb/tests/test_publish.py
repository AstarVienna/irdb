import copy
import os
from os import path as pth
from datetime import datetime as dt

import pytest
import yaml

from .. import publish as pub


PATH_TEST_PACKAGE_VERSION_YAML = pub.PKGS_DIR / "test_package" / "version.yaml"
NOW = dt.now().strftime("%Y-%m-%d")


@pytest.fixture(name="preserve_versions", scope="function")
def fixture_preserve_versions():
    """Preserve the versions of test packages."""

    # Backup version information.
    b_yaml_packages = pub.PATH_PACKAGES_YAML.read_bytes()
    b_yaml_test_package = PATH_TEST_PACKAGE_VERSION_YAML.read_bytes()
    b_pkgs = copy.deepcopy(pub.PKGS)

    # yield instead of return so the fixture can clean up afterwards
    yield

    # Put the original values back.
    pub.PATH_PACKAGES_YAML.write_bytes(b_yaml_packages)
    PATH_TEST_PACKAGE_VERSION_YAML.write_bytes(b_yaml_test_package)
    pub.PKGS = b_pkgs


def test_make_packages(preserve_versions):
    os.chdir(pth.join(pth.dirname(__file__), "../../"))
    pkg_name = "test_package"
    zip_name = pub.make_package(pkg_name, release="dev")

    assert zip_name == f"{pkg_name}.{NOW}.dev"
    assert pth.exists(pth.join("_ZIPPED_PACKAGES", zip_name+".zip"))

    version_dict = yaml.safe_load(open(PATH_TEST_PACKAGE_VERSION_YAML))
    assert version_dict["version"] == f"{NOW}.dev"


def test_run_main(preserve_versions):
    argv = ["", "-c", "test_package", "-p", "<insert_if_running_locally"]
    pub.main(argv)
    with open(PATH_TEST_PACKAGE_VERSION_YAML, encoding="utf8") as f:
        version_dict = yaml.safe_load(f)
    assert version_dict["version"] == NOW


def test_run_main_no_update_version():
    argv = ["", "-c", "test_package", "-p", "<insert_if_running_locally", "-d"]
    pub.main(argv)

    with open(PATH_TEST_PACKAGE_VERSION_YAML, encoding="utf8") as f:
        version_dict = yaml.safe_load(f)
    assert version_dict["version"] == "2022-07-11.dev"

    with open(pub.PATH_PACKAGES_YAML, encoding="utf8") as f:
        pckgs_dict = yaml.safe_load(f)
    assert pckgs_dict["test_package"]["stable"] == "test_package.2022-07-11"


def test_versions():
    """See whether the versions are compatible."""

    release_from_release = {
        "stable": "stable",
        "dev": "latest",
        "latest": "dev",
    }

    with open(pub.PATH_PACKAGES_YAML, encoding="utf8") as f:
        pckgs_dict = yaml.safe_load(f)

    for name, package_dict in pckgs_dict.items():
        path_version = pub.PKGS_DIR / name / "version.yaml"
        if not path_version.exists():
            # TODO: should this be disallowed?
            continue
        with open(path_version, encoding="utf8") as f:
            version_dict = yaml.safe_load(f)
            release_1 = version_dict["release"]
            version_1 = f"{name}.{version_dict['version']}"
            release_2 = release_from_release[release_1]
            version_2 = package_dict[release_2]
            assert version_1 == version_2


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
