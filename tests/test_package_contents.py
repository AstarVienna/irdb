import os
from os import path as pth
import glob

import yaml

from .utils import get_packages

PKG_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))
PKG_DICT = get_packages()


class TestFileStructureOfPackages:
    def test_all_packages_have_a_self_named_yaml(self):
        for pkg_name in PKG_DICT:
            assert pth.exists(pth.join(PKG_DICT[pkg_name], f"{pkg_name}.yaml"))

    def test_default_yaml_contains_packages_list(self):
        for pkg_name in PKG_DICT:
            default_yaml = pth.join(PKG_DICT[pkg_name], "default.yaml")
            if pth.exists(default_yaml):
                with open(default_yaml) as f:
                    yaml_dicts = [dic for dic in yaml.load_all(f)]

                assert len(yaml_dicts) > 0
                assert "packages" in yaml_dicts[0]
                assert "yamls" in yaml_dicts[0]
                assert f"{pkg_name}.yaml" in yaml_dicts[0]["yamls"]

