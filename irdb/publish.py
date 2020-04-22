import sys
import os
from os import path as pth
import shutil
from datetime import datetime as dt
import yaml
import pysftp


PKGS_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))
OLD_FILES = pth.join(PKGS_DIR, "_OLD_FILES")
ZIPPED_DIR = pth.join(PKGS_DIR, "_ZIPPED_PACKAGES")

SERVER_DIR = "./InstPkgSvr"
with open(pth.join(pth.dirname(__file__), "packages.yaml"), "r") as f:
    PKGS = yaml.load(f)


def publish(pkg_names=None, compile=True, upload=True):
    """
    Should be as easy as just calling this function to republish all packages

    .. note:: make sure that each package has an entry in the ``PKGS`` dict

    Parameters
    ----------
    pkg_names : list
    compile : bool
    upload : bool

    """
    if pkg_names is None:
        pkg_names = PKGS.keys()

    for pkg_name in pkg_names:
        if compile: make_packages(pkg_name)
        if upload: push_to_server(pkg_name)


def make_packages(pkg_names=()):
    if isinstance(pkg_names, str):
        pkg_names = [pkg_names]

    for pkg_name in pkg_names:
        old_pkg_path = pth.join(ZIPPED_DIR, pkg_name + ".zip")

        if pth.exists(old_pkg_path):
            new_path = rename_package(old_pkg_path)
            move_package(new_path, OLD_FILES)

        new_pkg_pth = zip_package_folder(pkg_name)
        move_package(new_pkg_pth, ZIPPED_DIR)
        print(f"[{str(dt.now())[:19]}]: Compiled package: {pkg_name}")


def rename_package(pkg_path):
    suffix = "." + str(dt.now().date())
    new_path = pkg_path.replace(".zip", suffix + ".zip")
    if pth.exists(new_path):
        os.remove(new_path)
    os.rename(pkg_path, new_path)

    return new_path


def move_package(pkg_path, dir_name):
    new_path = pth.join(dir_name, pth.basename(pkg_path))
    if pth.exists(new_path):
        os.remove(new_path)
    os.rename(pkg_path, new_path)


def zip_package_folder(pkg_name):
    pkg_dir = pth.join(PKGS_DIR, pkg_name)
    # new_pkg_path = shutil.make_archive(pkg_name, "zip", pkg_dir, pkg_name)
    new_pkg_path = shutil.make_archive(pkg_name, "zip", PKGS_DIR, pkg_name)

    return new_pkg_path


def push_to_server(pkg_name):
    local_path = pth.join(ZIPPED_DIR, pkg_name+".zip")

    if pkg_name not in PKGS:
        raise ValueError(f"{pkg_name} was not found in 'irdb/packages.yaml'")

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    sftp = pysftp.Connection(host="upload.univie.ac.at", username="simcado",
                             password="M1(aDo(aM", cnopts=cnopts)
    with sftp.cd("html/InstPkgSvr/"):
        if sftp.exists(PKGS[pkg_name]):
            sftp.remove(PKGS[pkg_name])
        sftp.put(local_path, PKGS[pkg_name])
        print(f"[{str(dt.now())[:19]}]: Pushed to server: {pkg_name}")


def print_help_menu():
    str = """Publish IRDB packages from the IRDB root directory:
    
python irdb/publish.py -cu <PKG_NAME> ... <PKG_NAME_N>
    
    -c, --compile : adds all files in a PKG folder to a .zip archive
    -u, --upload : uploads the PKG .zip archive to the server
    -h, --help : prints this statement 
    """
    print(str)


if __name__ == "__main__":
    _pkg_names = []
    if len(sys.argv) > 1:
        kwargs = {"compile": False, "upload": False}
        for arg in sys.argv[1:]:
            if "-" in arg:
                if "c" in arg: kwargs["compile"] = True
                if "u" in arg: kwargs["upload"] = True
                if "h" in arg: print_help_menu()
            else:
                _pkg_names += [arg]

        publish(_pkg_names, **kwargs)
