import os
from os import path as pth
import glob

PKG_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))


def get_packages():
    dirs = os.listdir(PKG_DIR)
    pkgs = {}
    for pkg in dirs:
        pkg_path = pth.abspath(pth.join(PKG_DIR, pkg))
        pkg_base = f"{pkg}.yaml"
        if pth.exists(pth.join(pkg_path, pkg_base)):
            pkgs[pkg] = pkg_path

    return pkgs
