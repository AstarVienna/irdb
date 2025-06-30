#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish and upload irdb packages"""

import argparse
import logging
import getpass
from typing import Optional
from warnings import warn
from pathlib import Path
from datetime import datetime as dt, timezone
from zipfile import ZIP_DEFLATED, ZipFile

import yaml
import pysftp

try:
    from .publish_utils import _is_stable, get_stable, get_all_package_versions
except ImportError:
    from publish_utils import _is_stable, get_stable, get_all_package_versions

# After 3.11, can just import UTC directly from datetime
UTC = timezone.utc

PATH_HERE = Path(__file__).parent
PKGS_DIR = PATH_HERE.parent
ZIPPED_DIR = PKGS_DIR / "_ZIPPED_PACKAGES"

PATH_FOLDERS_YAML = PATH_HERE / "server_folders.yaml"


class Password:
    """Used for secure pwd promt."""
    DEFAULT = "Prompt if not specified"

    def __init__(self, value):
        if value == self.DEFAULT:
            value = getpass.getpass("UniVie u:space password: ")
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError()
        return self.value == other.value


def publish(pkg_names=None, compilezip=False, upload=True,
            login=None, password=None, update_version=True):
    """
    Should be as easy as just calling this function to republish all packages

    Parameters
    ----------
    pkg_names : list
    compilezip : str, bool
        [False, "stable", "dev"]
    upload : bool
    login : str
    password : str
    update_version : bool
        True (default): update version in <pkg_name>/version.yaml
        False: use version in <pkg_name>/version.yaml
        See make_package().
    """
    warn(("This function is only kept for backwards compatibility and might "
          "be fully deprecated in the future."),
         PendingDeprecationWarning, stacklevel=2)
    for pkg_name in pkg_names:
        if compilezip:
            make_package(pkg_name,
                         stable=(compilezip == "stable"),
                         keep_version=not update_version)
        if upload:
            push_to_server(pkg_name, login=login, password=password)


def make_package(pkg_name: str, stable: bool = False,
                 keep_version: bool = False) -> str:
    """
    Makes a package (todo: update this description!)

    By default, make_package updates the version to today. `keep_version` can
    be set to True in order to use the existing version. This is a step towards
    a Continuous Deployment setup, where a new version is created first, and
    then a package will be uploaded (semi-)automatically.

    In practice, the `keep_version=True` functionality can also be used to
    retroactively upload a package that for some reason was not successfully
    uploaded.

    Parameters
    ----------
    pkg_name : str
        Name of the package (duh).
    stable : bool, optional
        Create a release that will be considered stable. The default is False.
    keep_version : bool, optional
        Keep the current version number the same. If False, the version number
        will be update to the current date. The default is False.

    Returns
    -------
    zip_name : str
        Name of the package's compiled zip file.

    """
    suffix = ".dev" if not stable else ""
    pkg_version_path = PKGS_DIR / pkg_name / "version.yaml"
    if not keep_version:
        # Collect the info for the version.yaml file
        time = dt.now(UTC)
        version_dict = {"version": f"{time.date()}{suffix}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "release": "stable" if stable else "dev"}

        # Add a version.yaml file to the package
        pkg_version_path.write_text(yaml.dump(version_dict), encoding="utf-8")
    else:
        # Load version info from current version.yaml file
        with pkg_version_path.open(encoding="utf-8") as file:
            version_dict = yaml.safe_load(file)
        time = dt.fromisoformat(version_dict["timestamp"])

    # Make the zip file
    zip_name = f"{pkg_name}.{time.date()}{suffix}.zip"
    zip_package_folder(pkg_name, zip_name)
    logging.info("[%s]: Compiled package: %s",
                 dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                 zip_name.strip(".zip"))

    return zip_name


def zip_package_folder(pkg_name: str, zip_name: str) -> Path:
    """
    Create a zip file of packages in `pkg_names`

    Directories `__pycache__` and hidden files (starting with `.`) are
    ignored.
    """
    src_path = (PKGS_DIR / pkg_name).expanduser().resolve(strict=True)
    # exclude any path containing any of the following anywhere
    excludes = {"__pycache__"}
    # ensure we don't end up with e.g. "foo.zip.zip":
    zip_pkg_path = (ZIPPED_DIR / zip_name).with_suffix(".zip")

    with ZipFile(zip_pkg_path, "w", ZIP_DEFLATED) as zip_file:
        files = (path for path in src_path.rglob("[!.]*")
                 if not any(excl in str(path) for excl in excludes))
        for file in files:
            zip_file.write(file, file.relative_to(src_path.parent))
    return zip_pkg_path



def _get_local_path(pkg_name: str, stable: bool) -> Path:
    try:
        zipped_versions = (path for path in ZIPPED_DIR.glob(f"{pkg_name}*.zip")
                           if _is_stable(path.stem) == stable)
        local_path = max(zipped_versions, key=lambda path: path.stem)
    except ValueError as err:
        raise ValueError(f"No compiled version of '{pkg_name}' found for "
                         f"condition '{stable=}'.") from err
    return local_path


def _handle_missing_folder(pkg_name: str):
    print(f"No server folder specified for package '{pkg_name}'.")
    proceed = input("Do you want to add a server folder now? Upload will be "
                    f"aborted otherwise. Also check spelling for '{pkg_name}' "
                    "before proceeding!    (y)/n:  ")
    if not proceed.lower() == "y":
        raise KeyboardInterrupt("Execution aborted by user.")

    new_folder = input("Allowed values for server folder are: 'locations', "
                       "'telescopes' and 'instruments':  ")
    if new_folder not in {"locations", "telescopes", "instruments"}:
        raise ValueError("Invalid input.")

    with PATH_FOLDERS_YAML.open("r", encoding="utf-8") as file:
        folders = yaml.safe_load(file)

    folders[pkg_name] = new_folder

    with PATH_FOLDERS_YAML.open("w", encoding="utf-8") as file:
        yaml.safe_dump(folders, file)

    return folders


def _get_server_path(pkg_name: str, local_name: str) -> str:
    with PATH_FOLDERS_YAML.open("r", encoding="utf-8") as file:
        folders = yaml.safe_load(file)
    try:
        server_path = f"{folders[pkg_name]}/{local_name}"
    except KeyError:
        folders = _handle_missing_folder(pkg_name)
        server_path = f"{folders[pkg_name]}/{local_name}"
    return server_path


def confirm(pkg_name: str) -> bool:
    """Ask for explicit user confirmation before pushing stable package."""
    try:
        current_stable = get_stable(get_all_package_versions()[pkg_name])
    except (KeyError, ValueError):
        current_stable = "<does not exist>"

    proceed = input("This will supersede the current STABLE version "
                    f"({current_stable}) of '{pkg_name}' on the IRDB server. "
                    "The uploaded package will be set as the new default "
                    f"for '{pkg_name}'.\nAre you sure you want to continue?"
                    "    (y)/n:  ")
    return proceed.lower() == "y"


def push_to_server(pkg_name: str, stable: bool = False,
                   login: Optional[str] = None,
                   password: Optional[Password] = None,
                   no_confirm: bool = False) -> None:
    """
    Upload a package to the univie server.

    Parameters
    ----------
    pkg_name : str
        Must have a compiled version locally available.
    stable : bool, optional
        If True, the latest compiled stable version will be pushed. If False,
        the lastest compiled dev version will be pushed. The default is False.
    login : Optional[str], optional
        Univie u:space username.
    password : Optional[str], optional
        Univie u:space password.

    Raises
    ------
    ValueError
        Raised if no compiled (stable) version of the package is found locally.

    Returns
    -------
    None

    """
    if password is None:
        raise ValueError("Password is None. Check email for password")

    local_path = _get_local_path(pkg_name, stable)
    server_path = _get_server_path(pkg_name, local_path.name)

    if not local_path.stem.endswith("dev") and not no_confirm and \
        not confirm(pkg_name):
        return

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    sftp = pysftp.Connection(host="webspace-access.univie.ac.at",
                             username=login, password=password.value,
                             cnopts=cnopts)

    with sftp.cd("scopesimu68/html/InstPkgSvr/"):
        if sftp.exists(server_path):
            sftp.remove(server_path)
        sftp.put(local_path, server_path)
        now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}]: Pushed to server: {pkg_name}")
    return


def push_packages_yaml_to_server(login, password):
    """
    Sync the packages.yaml file on the server with the current local one

    Parameters
    ----------
    login, password : str
        Univie u:space username and password

    """
    warn(("ANY use of packages.yaml is deprecated. "
          "No upload will be performed. "
          "This function will be removed in the next major release."),
         DeprecationWarning, stacklevel=2)


def main():
    """main CLI script"""
    parser = argparse.ArgumentParser(prog="publish",
        description=("Set a new version number, compile (zip) the specified "
                     "packages and (optionally) push them to the IRDB server. "
                     "This command must be run from the IRDB root directory."))

    parser.add_argument("pkg_names",
                        nargs="+",
                        help="Name(s) of the package(s).")
    parser.add_argument("-l",
                        dest="username",
                        required=True,
                        help=r"UniVie u:space username - e.g. u\kieranl14.")
    parser.add_argument("-p",
                        dest="password",
                        type=Password,
                        default=Password.DEFAULT,
                        help=("UniVie u:space password. If left empty, a "
                              "secure prompt will appear, which is the "
                              "recommended usage. Supplying the password "
                              "directly via this argument is unsecure and "
                              "only included for script support."))
    parser.add_argument("-c", "--compile",
                        action="store_true",
                        help="Compile all files in a PKG folder to a .zip archive.")
    parser.add_argument("-u", "--upload",
                        action="store_true",
                        help="Upload the package .zip archive to the server.")
    parser.add_argument("-s", "--stable",
                        action="store_true",
                        help=("Build as a stable version. By default, a dev "
                              "version is created. Publishing a stable version "
                              "requires to set this option, and a manual "
                              "conformation will be asked from the user."))
    parser.add_argument("-k", "--keep-version",
                        action="store_true",
                        help=("Keep the current package version number. "
                              "By default, running this script will bump the "
                              "package version number (date) and timestamp. "
                              "Set this option to prevent that."))
    parser.add_argument("--no-confirm",
                        action="store_true",
                        help=("Don't ask for confirmation when uploading "
                              "stable package. Only for CI/CD use!"))

    args = parser.parse_args()
    if args.compile:
        for pkg_name in args.pkg_names:
            make_package(pkg_name, args.stable, args.keep_version)
    if args.upload:
        for pkg_name in args.pkg_names:
            push_to_server(pkg_name, args.stable, args.username, args.password,
                           args.no_confirm)
    if not args.compile and not args.upload:
        logging.warning(("Neither `compile` nor `upload` was set. "
                         "No action will be performed."))


if __name__ == "__main__":
    main()
