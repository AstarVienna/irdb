"""Publish and upload irdb packages"""
import sys
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime as dt
import yaml
import pysftp

PATH_HERE = Path(__file__).parent
PKGS_DIR = PATH_HERE.parent
OLD_FILES = PKGS_DIR / "_OLD_FILES"
ZIPPED_DIR = PKGS_DIR / "_ZIPPED_PACKAGES"

SERVER_DIR = PATH_HERE / "InstPkgSvr"

HELPSTR = r"""
Publish stable IRDB packages
----------------------------
This command must be run from the IRDB root directory

$ python irdb/publish.py -c -u <PKG_NAME> ... <PKG_NAME_N> -l <USERNAME> -p <PASSWORD>

-l <USERNAME> : UniVie u:space username - e.g. u\kieranl14
-p <PASSWORD> : UniVie u:space password
-d : [update-version] : do not update the version of the package to today
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


with open(PATH_HERE / "packages.yaml", "r",
          encoding="utf8") as f_pkgs:
    PKGS = yaml.full_load(f_pkgs)


def publish(pkg_names=None, compilezip=False, upload=True,
            login=None, password=None, update_version=True):
    """
    Should be as easy as just calling this function to republish all packages

    .. note:: make sure that each package has an entry in the ``PKGS`` dict

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
    for pkg_name in pkg_names:
        if compilezip:
            make_package(pkg_name,
                         release=compilezip,
                         update_version=update_version)
        if upload:
            push_to_server(pkg_name, release=compilezip,
                           login=login, password=password)


def make_package(pkg_name=None, release="dev", update_version=True):
    """
    Makes a package

    Parameters
    ----------
    pkg_name : str
    release : str
        ["dev", "stable"]
    update_version : bool
        True (default): update version in <pkg_name>/version.yaml
        False: use version in <pkg_name>/version.yaml

    By default, make_package updates the version to today. update_version can
    be set to False in order to use the existing version. This is a step towards
    a Continuous Deployment setup, where a new version is created first, and
    then a package will be uploaded (semi-)automatically.

    In practice, the update_version=False functionality can also be used to
    retroactively upload a package that for some reason was not successfully
    uploaded.
    """
    assert pkg_name in PKGS, f"{pkg_name} not found in {PKGS.keys()}"

    pkg_version_path = PKGS_DIR / pkg_name / "version.yaml"
    if update_version:
        # Collect the info for the version.yaml file
        timestamp = str(dt.now())[:19]
        suffix = ".dev" if release == "dev" else ""
        version_dict = {"version": f"{timestamp[:10]}{suffix}",
                        "timestamp": timestamp,
                        "release": release}

        # Add a version.yaml file to the package
        with open(pkg_version_path, "w", encoding="utf8") as f:
            yaml.dump(version_dict, f)
    else:
        with open(pkg_version_path, encoding="utf8") as f:
            version_dict = yaml.safe_load(f)
        timestamp = version_dict["timestamp"]
        release = version_dict["release"]
        suffix = ".dev" if release == "dev" else ""

    # Make the zip file
    zip_name = f"{pkg_name}.{timestamp[:10]}{suffix}"
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
        shutil.copytree(PKGS_DIR / pkg_name,
                        Path(tmpdir) / pkg_name,
                        symlinks=True,
                        ignore=ignore_patterns)
        new_pkg_path = shutil.make_archive(ZIPPED_DIR / zip_name,
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
    local_path = ZIPPED_DIR / f"{zip_name}.zip"
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
    local_path = PKGS_DIR / "irdb" / "packages.yaml"
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
        kwargs = {"compilezip": False, "upload": False, "update_version": True}
        argv_iter = iter(argv[1:])
        for arg in argv_iter:
            if "-" in arg:
                if "l" in arg:
                    kwargs["login"] = next(argv_iter)
                if "p" in arg:
                    kwargs["password"] = next(argv_iter)
                if "c" in arg:
                    kwargs["compilezip"] = "dev" if "dev" in arg else "stable"
                if "u" in arg:
                    kwargs["upload"] = True
                if "d" in arg:
                    kwargs["update_version"] = False
                if "h" in arg:
                    print(HELPSTR)
                    sys.exit()
            else:
                if arg.lower() == "all":
                    _pkg_names = PKGS.keys()
                else:
                    _pkg_names += [arg]

        publish(_pkg_names, **kwargs)

        with open(PATH_HERE / "packages.yaml", "w",
                  encoding="utf8") as f:
            yaml.dump(PKGS, f)

        push_packages_yaml_to_server(login=kwargs["login"],
                                     password=kwargs["password"])


if __name__ == "__main__":
    main(sys.argv)
