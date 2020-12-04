from os import path as pth
from glob import glob
import yaml

from irdb.utils import get_packages, load_badge_yaml, write_badge_yaml, \
    recursive_filename_search

PKG_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))
PKG_DICT = get_packages()
BADGES = load_badge_yaml()


def teardown_module():
    write_badge_yaml(BADGES)


class TestFileStructureOfPackages:
    def test_all_packages_have_a_self_named_yaml(self):
        for pkg_name in PKG_DICT:
            result = pth.exists(pth.join(PKG_DICT[pkg_name], f"{pkg_name}.yaml"))
            BADGES[f"!{pkg_name}.structure.self_named_yaml"] = result

    def test_default_yaml_contains_packages_list(self):
        for pkg_name in PKG_DICT:
            default_yaml = pth.join(PKG_DICT[pkg_name], "default.yaml")
            if pth.exists(default_yaml):
                with open(default_yaml) as f:
                    yaml_dicts = [dic for dic in yaml.load_all(f)]

                result = "packages" in yaml_dicts[0] and \
                         "yamls" in yaml_dicts[0] and \
                         f"{pkg_name}.yaml" in yaml_dicts[0]["yamls"]
                BADGES[f"!{pkg_name}.structure.default_yaml"] = result

                BADGES[f"!{pkg_name}.package_type"] = "observation"
            else:
                BADGES[f"!{pkg_name}.package_type"] = "support"

    def test_all_files_referenced_in_yamls_exist(self):
        for pkg_name in PKG_DICT:

            no_missing = 0
            yaml_files = glob(PKG_DICT[pkg_name]+"/*.yaml")
            for yaml_file in yaml_files:
                with open(yaml_file) as f:
                    try:
                        yaml_dicts = [dic for dic in yaml.load_all(f)]
                    except:
                        yaml_dicts = []

                fnames = []
                for yaml_dict in yaml_dicts:
                    fnames += recursive_filename_search(yaml_dict)

                for fname in fnames:
                    if fname is not None:
                        if not isinstance(fname, (list, tuple)):
                            fname = [fname]
                        for fn in fname:
                            if fn.lower() != "none" and fn[0] != "!":
                                full_fname = pth.join(PKG_DICT[pkg_name], fn)
                                if not pth.exists(full_fname):
                                    BADGES[pkg_name]["structure"][fn] = "missing"
                                    no_missing += 1

            if no_missing == 0:
                BADGES[f"!{pkg_name}.structure.no_missing_files"] = True

    def test_all_yaml_files_readable(self):
        for pkg_name in PKG_DICT:

            yaml_files = glob(PKG_DICT[pkg_name]+"/*.yaml")
            no_errors = 0
            for yaml_file in yaml_files:
                with open(yaml_file) as f:
                    try:
                        yaml_dicts = [dic for dic in yaml.load_all(f)]
                    except:
                        no_errors += 1
                        BADGES[f"!{pkg_name}.contents"][pth.basename(yaml_file)] = "error"

            if no_errors == 0:
                BADGES[f"!{pkg_name}.contents.all_yamls_readable"] = True


