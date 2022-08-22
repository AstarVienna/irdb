from os import path as p
import yaml
from tempfile import TemporaryDirectory

dname = p.dirname(__file__)
with open(p.join(dname, "packages.yaml")) as f:
    PKGS = yaml.full_load(f)


def __getattr__(name):
    if name not in PKGS:
        raise ImportError(f"{name} not in irdb.PKGS dictionary")

    return PKGS[name]
