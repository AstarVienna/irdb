import os
from os import path as pth
import shutil
from datetime import datetime as dt
import pysftp


PKGS_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))
OLD_FILES = pth.join(PKGS_DIR, "_OLD_FILES")
ZIPPED_DIR = pth.join(PKGS_DIR, "_ZIPPED_PACKAGES")

SERVER_DIR = "./InstPkgSvr"
PKGS = {"Armazones": "locations/Armazones.zip",
        "ELT": "telescopes/ELT.zip",
        "MAORY": "instruments/MAORY.zip",
        "MICADO": "instruments/MICADO.zip",
        "test_package": "instruments/test_package.zip"}


def publish(pkg_names=("Armazones", "ELT", "MAORY", "MICADO")):
    """
    Should be as easy as just calling this function to republish all packages

    .. note:: make sure that each package has an entry in the ``PKGS`` dict

    Parameters
    ----------
    pkg_names : list

    """
    make_packages(pkg_names)
    for pkg_name in pkg_names:
        push_to_server(pkg_name)


def make_packages(pkg_names=()):
    for pkg_name in pkg_names:
        old_pkg_path = pth.join(ZIPPED_DIR, pkg_name + ".zip")

        if pth.exists(old_pkg_path):
            new_path = rename_package(old_pkg_path)
            move_package(new_path, OLD_FILES)

        pkg_dir = pth.join(PKGS_DIR, pkg_name)
        new_pkg_pth = zip_package_folder(pkg_name)
        move_package(new_pkg_pth, ZIPPED_DIR)


def rename_package(pkg_path):
    suffix = "." + str(dt.now().date())
    new_path = pkg_path.replace(".zip", suffix + ".zip")
    os.rename(pkg_path, new_path)

    return new_path


def move_package(pkg_path, dir_name):
    new_path = pth.join(dir_name, pth.basename(pkg_path))
    if pth.exists(new_path):
        os.remove(new_path)
    os.rename(pkg_path, new_path)


def zip_package_folder(pkg_name):
    pkg_dir = pth.join(PKGS_DIR, pkg_name)
    new_pkg_path = shutil.make_archive(pkg_dir, "zip", "./", pkg_dir)

    return new_pkg_path


def push_to_server(pkg_name):
    local_path = pth.join(ZIPPED_DIR, pkg_name+".zip")

    sftp = pysftp.Connection(host="upload.univie.ac.at", username="simcado",
                             password="M1(aDo(aM")
    with sftp.cd(f"html/InstPkgSvr/"):
        if sftp.exists(PKGS[pkg_name]):
            sftp.remove(PKGS[pkg_name])
        sftp.put(local_path, PKGS[pkg_name])
