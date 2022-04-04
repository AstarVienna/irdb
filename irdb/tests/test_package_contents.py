from os import path as pth
from glob import glob

import pytest
import yaml

from scopesim.effects.data_container import DataContainer
from astropy.io.ascii import InconsistentTableError

from irdb.utils import get_packages, load_badge_yaml, write_badge_yaml, \
    recursive_filename_search

PKG_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
PKG_DICT = get_packages()
BADGES = load_badge_yaml()


def teardown_module():
    write_badge_yaml(BADGES)


class TestFileStructureOfPackages:
    def test_all_packages_have_a_self_named_yaml(self):
        """This test can never fail.

        get_packages() decides whether a directory is a package based on
        whether it has a yaml file in it with the same name.
        """
        bad_packages = []
        for pkg_name in PKG_DICT:
            result = pth.exists(pth.join(PKG_DICT[pkg_name], f"{pkg_name}.yaml"))
            BADGES[f"!{pkg_name}.structure.self_named_yaml"] = result
            if not result:
                bad_packages.append(pkg_name)
        assert not bad_packages

    def test_default_yaml_contains_packages_list(self):
        bad_packages = []
        for pkg_name in PKG_DICT:
            default_yaml = pth.join(PKG_DICT[pkg_name], "default.yaml")
            if pth.exists(default_yaml):
                with open(default_yaml) as f:
                    yaml_dicts = [dic for dic in yaml.full_load_all(f)]

                result = "packages" in yaml_dicts[0] and \
                         "yamls" in yaml_dicts[0] and \
                         f"{pkg_name}.yaml" in yaml_dicts[0]["yamls"]
                BADGES[f"!{pkg_name}.structure.default_yaml"] = result
                if not result:
                    bad_packages.append(pkg_name)

                BADGES[f"!{pkg_name}.package_type"] = "observation"
            else:
                BADGES[f"!{pkg_name}.package_type"] = "support"
        assert not bad_packages

    @pytest.mark.xfail(
        reason="Most of the missing files seem to exist in other packages though, so they are probably okay."
    )
    def test_all_files_referenced_in_yamls_exist(self):
        missing_files = []
        for pkg_name in PKG_DICT:

            no_missing = 0
            yaml_files = glob(PKG_DICT[pkg_name]+"/*.yaml")
            for yaml_file in yaml_files:
                with open(yaml_file) as f:
                    try:
                        yaml_dicts = [dic for dic in yaml.full_load_all(f)]
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
                                    missing_files += [full_fname]

            if no_missing == 0:
                BADGES[f"!{pkg_name}.structure.no_missing_files"] = True
        assert not missing_files, f"{missing_files}"

    def test_all_yaml_files_readable(self):
        yamls_bad = []
        for pkg_name in PKG_DICT:
            yaml_files = glob(PKG_DICT[pkg_name]+"/*.yaml")
            no_errors = 0
            for yaml_file in yaml_files:
                with open(yaml_file) as f:
                    try:
                        yaml_dicts = [dic for dic in yaml.full_load_all(f)]
                    except:
                        no_errors += 1
                        yamls_bad += [yaml_file]
                        BADGES[f"!{pkg_name}.contents"][pth.basename(yaml_file)] = "error"

            if no_errors == 0:
                BADGES[f"!{pkg_name}.contents.all_yamls_readable"] = True
        assert not yamls_bad, f"Errors found in yaml files: {yamls_bad}"

    def test_all_dat_files_readable(self):
        bad_files = []
        fns_dat = glob(PKG_DIR + "/**/*.dat")
        assert fns_dat
        for fn_dat in fns_dat:
            try:
                datacont = DataContainer(fn_dat)
            except InconsistentTableError as e:
                print(fn_dat, "InconsistentTableError", e)
                bad_files.append(fn_dat)
            except ValueError as e:
                print(fn_dat, "ValeError", e)
                bad_files.append(fn_dat)
            except Exception as e:
                print(fn_dat, "Unexpected Exception", e.__class__, e)
                bad_files.append(fn_dat)
        assert not bad_files, bad_files

