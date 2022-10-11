"""Publish and upload irdb packages"""
import sys
from os import path as pth
import shutil
from tempfile import TemporaryDirectory
from datetime import datetime as dt
import yaml
import pysftp

PKGS_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))
OLD_FILES = pth.join(PKGS_DIR, "_OLD_FILES")
ZIPPED_DIR = pth.join(PKGS_DIR, "_ZIPPED_PACKAGES")

SERVER_DIR = "./InstPkgSvr"

HELPSTR = """
Publish stable IRDB packages
----------------------------
This command must be run from the IRDB root directory

$ python irdb/publish.py -c -u <PKG_NAME> ... <PKG_NAME_N> -l <USERNAME> -p <PASSWORD>

-l <USERNAME> : UniVie u:space username - e.g. u\kieranl14
-p <PASSWORD> : UniVie u:space password
-c : [compile] all files in a PKG folder to a .zip archive
-cdev : [compile-dev] like compile, but tags as development version
-u : [upload] the PKG .zip archive to the server
-h : [help] prints this statement

Arguments without a "-" are assumed to be package names, except for username and password


Publish development versions
----------------------------
To compile and upload a development version, use the cdev tag

$ python irdb/publish.py -cdev -u <PKG_NAME> ... <PKG_NAME_N> -l <USERNAME> -p <PASSWORD>

"""


with open(pth.join(pth.dirname(__file__), "packages.yaml"), "r",
          encoding="utf8") as f:
    PKGS = yaml.full_load(f)


def publish(pkg_names=None, compile=False, upload=True,
            login=None, password=None):
    """
    Should be as easy as just calling this function to republish all packages

    .. note:: make sure that each package has an entry in the ``PKGS`` dict

    Parameters
    ----------
    pkg_names : list
    compile : str, bool
        [False, "stable", "dev"]
    upload : bool
    password : str

    """
    for pkg_name in pkg_names:
        if compile:
            make_package(pkg_name, release=compile)
        if upload:
            push_to_server(pkg_name, release=compile,
                           login=login, password=password)


def make_package(pkg_name=None, release="dev"):
    """
    Makes a package

    Parameters
    ----------
    pkg_name : str
    release : str
        ["dev", "stable"]

    """
    if pkg_name in PKGS:
        # Collect the info for the version.yaml file
        timestamp = str(dt.now())[:19]
        suffix = ".dev" if release == "dev" else ""
        zip_name = f"{pkg_name}.{timestamp[:10]}{suffix}"
        version_dict = {"version": f"{timestamp[:10]}{suffix}",
                        "timestamp": timestamp,
                        "release": release}

        # Add a version.yaml file to the package
        pkg_version_path = pth.join(pkg_name, "version.yaml")
        with open(pkg_version_path, "w") as f:
            yaml.dump(version_dict, f)

        # Make the zip file
        zip_package_folder(pkg_name, zip_name)
        print(f"[{timestamp}]: Compiled package: {zip_name}")

        # Update the global dict of packages
        PKGS[pkg_name]["latest"] = zip_name
        if release == "stable":
            PKGS[pkg_name]["stable"] = zip_name

    return zip_name


def zip_package_folder(pkg_name, zip_name):
    """
    Create a zip file of packages in `pkg_names`

    Directories `__pycache__` and hidden files (starting with `.`) are
    ignored.
    """
    ignore_patterns = shutil.ignore_patterns("__pycache__", ".*")
    with TemporaryDirectory() as tmpdir:
        shutil.copytree(pth.join(PKGS_DIR, pkg_name),
                        pth.join(tmpdir, pkg_name),
                        ignore=ignore_patterns)
        new_pkg_path = shutil.make_archive(pth.join(ZIPPED_DIR, zip_name),
                                           "zip", tmpdir, pkg_name)

    return new_pkg_path


def push_to_server(pkg_name, release="stable", login=None, password=None):
    """
    Upload a package to the univie server

    Parameters
    ----------
    pkg_name : str
        An entry from packages.yaml
    release : str
        ["dev", "stable"]
    login, password : str
        Univie u:space username and password

    """
    if password is None:
        raise ValueError("Password is None. Check email for password")

    if pkg_name not in PKGS:
        raise ValueError(f"{pkg_name} was not found in 'irdb/packages.yaml'")

    version = "latest" if release == "dev" else "stable"
    zip_name = PKGS[pkg_name][version]
    local_path = pth.join(ZIPPED_DIR, f"{zip_name}.zip")
    server_dir = PKGS[pkg_name]["path"]
    server_path = f"{server_dir}/{zip_name}.zip"

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    sftp = pysftp.Connection(host="webspace-access.univie.ac.at",
                             username=login, password=password, cnopts=cnopts)

    with sftp.cd("scopesimu68/html/InstPkgSvr/"):
        if sftp.exists(server_path):
            sftp.remove(server_path)
        sftp.put(local_path, server_path)
        print(f"[{str(dt.now())[:19]}]: Pushed to server: {pkg_name}")


def push_packages_yaml_to_server(login, password):
    """
    Sync the packages.yaml file on the server with the current local one

    Parameters
    ----------
    login, password : str
        Univie u:space username and password

    """
    local_path = pth.join(PKGS_DIR, "irdb", "packages.yaml")
    server_path = "packages.yaml"

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    sftp = pysftp.Connection(host="webspace-access.univie.ac.at",
                             username=login, password=password, cnopts=cnopts)
    # with sftp.cd("html/InstPkgSvr/"):
    with sftp.cd("scopesimu68/html/InstPkgSvr/"):
        sftp.put(local_path, server_path)
        print(f"[{str(dt.now())[:19]}]: Pushed to server: packages.yaml")


def main(argv):
    """
    $ python irdb/publish.py -c -u <PKG_NAME> ... <PKG_NAME_N> -l <USERNAME> -p <PASSWORD>
    """
    _pkg_names = []
    if len(argv) > 1:
        kwargs = {"compile": False, "upload": False}
        argv_iter = iter(argv[1:])
        for arg in argv_iter:
            if "-" in arg:
                if "l" in arg:
                    kwargs["login"] = next(argv_iter)
                if "p" in arg:
                    kwargs["password"] = next(argv_iter)
                if "c" in arg:
                    kwargs["compile"] = "dev" if "dev" in arg else "stable"
                if "u" in arg:
                    kwargs["upload"] = True
                if "h" in arg:
                    print(HELPSTR)
            else:
                if arg.lower() == "all":
                    _pkg_names = PKGS.keys()
                else:
                    _pkg_names += [arg]

        publish(_pkg_names, **kwargs)

        with open(pth.join(pth.dirname(__file__), "packages.yaml"), "w",
                  encoding="utf8") as f:
            yaml.dump(PKGS, f)

        push_packages_yaml_to_server(login=kwargs["login"],
                                     password=kwargs["password"])


if __name__ == "__main__":
    main(sys.argv)
