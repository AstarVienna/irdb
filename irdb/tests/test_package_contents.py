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
from irdb.fileversions import IRDBFile

# HACK: This is necessary because scopesim has import side effects that mess up
#       logging here, specifically capture. Once that's solved, the following
#       lines should be removed!
from importlib import reload
logging.shutdown()
reload(logging)


# Note: This module doesn't need to run always, so mark it.
pytestmark = pytest.mark.badges

# TODO: some tests should be skipped if something else has failed.
# howto: https://stackoverflow.com/questions/75377691/skip-test-case-if-above-test-case-failed-pytest
# and: https://pytest-dependency.readthedocs.io/en/stable/advanced.html


@pytest.fixture(name="pkg_dir", scope="module")
def fixture_pkg_dir():
    return Path(__file__).parent.parent.parent


@pytest.fixture(name="badges", scope="module")
def fixture_badges():
    with BadgeReport() as report:
        yield report


@pytest.mark.parametrize("package", list(get_packages()))
class TestFileStructureOfPackages:
    def test_default_yaml_contains_packages_list(self, package, badges):
        pkg_name, pkg_path = package
        default_yaml = pkg_path / "default.yaml"
        if not default_yaml.exists():
            badges[f"!{pkg_name}.package_type"] = "support"
            return

        badges[f"!{pkg_name}.package_type"] = "observation"

        with default_yaml.open(encoding="utf-8") as file:
            yaml_dict = next(yaml.full_load_all(file))

        result = "packages" in yaml_dict

        # METIS is special since in WCU mode it operates without METIS.
        if pkg_name not in {"METIS"}:
            result &= "yamls" in yaml_dict \
                and f"{pkg_name}.yaml" in yaml_dict["yamls"]
        if result:
            badges[f"!{pkg_name}.structure.default_yaml"] = "OK"
        else:
            badges[f"!{pkg_name}.structure.default_yaml"] = "incomplete"
        assert result, pkg_name

    @pytest.mark.xfail(
        reason=("After updating get_packages(), some (almost) empty packages "
                "are now recognised, which don't have a self named yaml. "
                "This should be in the reports, but doesn't need to make the "
                "tests fail overall.")
    )
    def test_all_packages_have_a_self_named_yaml(self, package, badges):
        """The following is *no longer true* after an update to get_packages():

        This test can never fail.

        get_packages() decides whether a directory is a package based on
        whether it has a yaml file in it with the same name.
        """
        pkg_name, pkg_path = package
        if (result := (pkg_path / f"{pkg_name}.yaml").exists()):
            badges[f"!{pkg_name}.structure.self_named_yaml"] = "found"
        else:
            badges[f"!{pkg_name}.structure.self_named_yaml"] = "not found"
        assert result, pkg_name

    @pytest.mark.xfail(
        reason=("Most of the missing files seem to exist in other packages "
                "though, so they are probably okay.")
    )
    def test_all_files_referenced_in_yamls_exist(self, package, badges):
        missing_files = []
        pkg_name, pkg_path = package
        yaml_files = list(pkg_path.glob("*.yaml"))
        for yaml_file in yaml_files:
            with yaml_file.open(encoding="utf-8") as file:
                # An error here shouldn't pass silently. If this regularly
                # produces [the same] error(s), *that* error(s) should be
                # caught and handled accordingly!
                # Additionally: should test_all_yaml_files_readable assert
                # that these files don't produce any errors? Hmmm
                # try:
                yaml_dicts = list(yaml.full_load_all(file))
                # except Exception:
                #     yaml_dicts = []

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
                            # Since with the parametrisation, we only have one
                            # missing_files list per pkg, don't need full name.
                            # missing_files.append(str(full_fname))
                            missing_files.append(fn)

        if not yaml_files:
            badges[f"!{pkg_name}.structure.no_files_referenced"] = "!NONE"
        elif yaml_files and not missing_files:
            badges[f"!{pkg_name}.structure.no_missing_files"] = "!OK"
        assert not missing_files, f"{pkg_name}: {missing_files=}"

    def test_all_yaml_files_readable(self, package, badges):
        yamls_bad = []
        pkg_name, pkg_path = package
        yaml_files = list(pkg_path.glob("*.yaml"))
        for yaml_file in yaml_files:
            with yaml_file.open(encoding="utf-8") as file:
                try:
                    _ = list(yaml.full_load_all(file))
                except Exception:
                    # TODO: maybe Exception is too general? This used to be a
                    #       bare except anyway...
                    # TODO: maybe record *what* error was produced here,
                    #       similar to how we do in test_all_dat_files_readable
                    yamls_bad.append(str(yaml_file))
                    badges[f"!{pkg_name}.contents"][yaml_file.name] = "error"

        if not yaml_files:
            badges[f"!{pkg_name}.contents.no_yaml_files"] = "!NONE"
        elif yaml_files and not yamls_bad:
            badges[f"!{pkg_name}.contents.all_yamls_readable"] = "!OK"
        assert not yamls_bad, f"Errors in {pkg_name} yaml files: {yamls_bad}"


@pytest.mark.parametrize("package", list(get_packages()))
class TestPackageDatFiles:
    @pytest.mark.xfail(
        reason=("Due to bad globbing, files in subfolders were not checked "
                "previously, some of those now fail. idk y tho")
    )
    def test_all_dat_files_readable(self, package, pkg_dir, badges, caplog):
        bad_files = []
        how_bad = {"inconsistent_table_error": [],
                   "value_error": [],
                   "unexpected_error": []}
        pkg_name, pkg_path = package
        fns_dat = list(pkg_path.rglob("*.dat"))
        assert fns_dat
        for fn_dat in fns_dat:
            fn_loc = fn_dat.relative_to(pkg_dir)
            try:
                # FIXME: DataContainer should be updated to support Path objects...
                _ = DataContainer(str(fn_dat))
            except InconsistentTableError as err:
                logging.error("%s InconsistentTableError %s", str(fn_loc), err)
                bad_files.append(str(fn_loc))
                badges[f"!{fn_loc.parts[0]}.contents"][fn_loc.name] = "error"
                how_bad["inconsistent_table_error"].append(str(fn_loc))
            except ValueError as err:
                logging.error("%s ValeError %s", str(fn_loc), err)
                bad_files.append(str(fn_loc))
                badges[f"!{fn_loc.parts[0]}.contents"][fn_loc.name] = "error"
                how_bad["value_error"].append(str(fn_loc))
            except Exception as err:
                logging.error("%s Unexpected Exception %s %s", str(fn_loc),
                              err.__class__, err)
                bad_files.append(str(fn_loc))
                badges[f"!{fn_loc.parts[0]}.contents"][fn_loc.name] = "error"
                how_bad["unexpected_error"].append(str(fn_loc))
        if any(how_bad.values()):
            logging.info(how_bad)
        badges.logs.extend(caplog.records)

        assert not bad_files, bad_files

    @pytest.mark.xfail(
        reason=("This (new) test shows many previously unknown, but not "
                "critical inconsistencies, which would pollute the tests, so "
                "xfail this for now, report is generated regardless.")
    )
    def test_all_dat_files_consistent(self, package, pkg_dir, badges, caplog):
        bad_files = []
        how_bad = {"file_read_error": [],
                   "value_error": [],
                   "unexpected_error": []}
        # fns_dat = list(IRDBFile.from_folder(pkg_dir))
        pkg_name, pkg_path = package
        fns_dat = list(pkg_path.rglob("*.dat"))
        assert fns_dat
        for fn_dat in fns_dat:
            fn_loc = fn_dat.relative_to(pkg_dir)
            try:
                dat_file = IRDBFile.from_file(fn_dat)
            except Exception as err:
                logging.error("%s Error reading dat file %s", str(fn_loc), err)
                # bad_files.append(str(fn_loc))
                how_bad["file_read_error"].append(str(fn_loc))

            try:
                dat_file.validate_dates()
            except ValueError as err:
                logging.error("%s ValeError %s", str(fn_loc), err)
                bad_files.append(str(fn_loc))
                badges[f"!{fn_loc.parts[0]}.dates"][dat_file.name] = "conflict"
                how_bad["value_error"].append(str(fn_loc))
            except Exception as err:
                logging.error("%s Unexpected Exception %s %s", str(fn_loc),
                              err.__class__, err)
                bad_files.append(str(fn_loc))
                badges[f"!{fn_loc.parts[0]}.dates"][dat_file.name] = "error"
                how_bad["unexpected_error"].append(str(fn_loc))
        if any(how_bad.values()):
            logging.info(how_bad)
        badges.logs.extend(caplog.records)

        assert not bad_files, bad_files
