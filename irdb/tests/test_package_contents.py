#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import pytest
import yaml

from scopesim.effects.data_container import DataContainer
from astropy.io.ascii import InconsistentTableError

from irdb.utils import get_packages, recursive_filename_search
from irdb.badges import BadgeReport

PKG_DIR = Path(__file__).parent.parent.parent
PKG_DICT = dict(get_packages())


@pytest.fixture(scope="class")
def badges():
    with BadgeReport() as report:
        yield report


class TestFileStructureOfPackages:
    def test_all_packages_have_a_self_named_yaml(self, badges):
        """This test can never fail.

        get_packages() decides whether a directory is a package based on
        whether it has a yaml file in it with the same name.
        """
        bad_packages = []
        for pkg_name, pkg_path in PKG_DICT.items():
            if (pkg_path / f"{pkg_name}.yaml").exists():
                badges[f"!{pkg_name}.structure.self_named_yaml"] = "found"
            else:
                badges[f"!{pkg_name}.structure.self_named_yaml"] = "not found"
                bad_packages.append(pkg_name)
        assert not bad_packages

    def test_default_yaml_contains_packages_list(self, badges):
        bad_packages = []
        for pkg_name, pkg_path in PKG_DICT.items():
            default_yaml = pkg_path / "default.yaml"
            if not default_yaml.exists():
                badges[f"!{pkg_name}.package_type"] = "support"
                continue

            with default_yaml.open(encoding="utf-8") as file:
                yaml_dict = next(yaml.full_load_all(file))

            result = "packages" in yaml_dict and "yamls" in yaml_dict and \
                     f"{pkg_name}.yaml" in yaml_dict["yamls"]
            if result:
                badges[f"!{pkg_name}.structure.default_yaml"] = "OK"
            else:
                badges[f"!{pkg_name}.structure.default_yaml"] = "incomplete"
                bad_packages.append(pkg_name)

            badges[f"!{pkg_name}.package_type"] = "observation"

        assert not bad_packages

    @pytest.mark.xfail(
        reason="Most of the missing files seem to exist in other packages though, so they are probably okay."
    )
    def test_all_files_referenced_in_yamls_exist(self, badges):
        missing_files = []
        for pkg_name, pkg_path in PKG_DICT.items():

            num_missing = 0
            for yaml_file in pkg_path.glob("*.yaml"):
                with yaml_file.open(encoding="utf-8") as file:
                    try:
                        yaml_dicts = list(yaml.full_load_all(file))
                    except Exception:
                        yaml_dicts = []

                fnames = []
                for yaml_dict in yaml_dicts:
                    fnames.extend(recursive_filename_search(yaml_dict))

                for fname in fnames:
                    if fname is None:
                        continue
                    if not isinstance(fname, (list, tuple)):
                        fname = [fname]
                    for fn in fname:
                        if fn.lower() != "none" and not fn.startswith("!"):
                            full_fname = pkg_path / fn
                            if not full_fname.exists():
                                badges[pkg_name]["structure"][fn] = "missing"
                                num_missing += 1
                                missing_files.append(str(full_fname))

            if not num_missing:
                badges[f"!{pkg_name}.structure.no_missing_files"] = "!OK"
        assert not missing_files, f"{missing_files}"

    def test_all_yaml_files_readable(self, badges):
        yamls_bad = []
        for pkg_name, pkg_path in PKG_DICT.items():
            num_errors = 0
            for yaml_file in pkg_path.glob("*.yaml"):
                with yaml_file.open(encoding="utf-8") as file:
                    try:
                        _ = list(yaml.full_load_all(file))
                    except Exception:
                        num_errors += 1
                        yamls_bad.append(str(yaml_file))
                        badges[f"!{pkg_name}.contents"][yaml_file.name] = "error"

            if not num_errors:
                badges[f"!{pkg_name}.contents.all_yamls_readable"] = "!OK"
        assert not yamls_bad, f"Errors found in yaml files: {yamls_bad}"

    @pytest.mark.xfail
    def test_all_dat_files_readable(self, badges):
        bad_files = []
        how_bad = {"inconsistent_table_error": [],
                   "value_error": [],
                   "unexpected_error": []}
        fns_dat = PKG_DIR.rglob("*.dat")
        # TODO: the following assert now always passed because fns_dat is a
        #       generator object (while the check was likely meant to catch
        #       empty lists)
        assert fns_dat
        for fn_dat in fns_dat:
            fn_loc = fn_dat.relative_to(PKG_DIR)
            try:
                # FIXME: DataContainer should be updated to support Path objects...
                _ = DataContainer(str(fn_dat))
            except InconsistentTableError as err:
                logging.error("%s InconsistentTableError %s", str(fn_loc), err)
                bad_files.append(fn_loc)
                badges[f"!{fn_loc.parts[0]}.contents"][fn_loc.name] = "error"
                how_bad["inconsistent_table_error"].append(fn_loc)
            except ValueError as err:
                logging.error("%s ValeError %s", str(fn_loc), err)
                bad_files.append(fn_loc)
                badges[f"!{fn_loc.parts[0]}.contents"][fn_loc.name] = "error"
                how_bad["value_error"].append(fn_loc)
            except Exception as err:
                logging.error("%s Unexpected Exception %s %s", str(fn_loc),
                              err.__class__, err)
                bad_files.append(fn_loc)
                badges[f"!{fn_loc.parts[0]}.contents"][fn_loc.name] = "error"
                how_bad["unexpected_error"].append(fn_loc)
        logging.warning(how_bad)

        assert not bad_files, bad_files
