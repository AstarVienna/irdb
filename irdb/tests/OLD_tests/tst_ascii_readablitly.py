import os
import inspect
import warnings
from glob import glob

import yaml
from astropy.io import ascii as ioascii
from astropy.table import Table

# Tests for the ascii files:
# 1. Test astropy.io.ascii can return a table object for each file
# 2. Test that each ASCII header can be converted to a dictionary by pyYAML
# 3. Specific tests for each type of ASCII file

cur_frame = os.path.dirname(inspect.getfile(inspect.currentframe()))
HOME = os.path.abspath(os.path.join(cur_frame, "../"))
REPORTS = os.path.abspath(os.path.join(HOME, "_REPORTS"))

with open(os.path.join(HOME, "packages.yaml")) as f:
    PKGS_DICT = yaml.full_load(f)


def get_ascii_files_in_package(pkg_dir):
    if not os.path.exists(pkg_dir):
        raise ValueError("{} doesn't exist".format(pkg_dir))

    ascii_tags = [".dat", ".tbl"]
    files = []
    for tag in ascii_tags:
        files += glob(os.path.join(pkg_dir, "*"+tag))

    return files


def convert_table_comments_to_dict(tbl):

    comments_dict = None
    if "comments" in tbl.meta:
        try:
            comments_dict = yaml.full_load("\n".join(tbl.meta["comments"]))
        except:
            warnings.warn("Couldn't convert <table>.meta['comments'] to dict")
            comments_dict = tbl.meta["comments"]
    else:
        warnings.warn("No comments in table")

    return comments_dict


def write_report(filename, dic, tag):
    passing_url = "[![](https://img.shields.io/badge/{}-passing-green.svg)]()"
    failing_url = "[![](https://img.shields.io/badge/{}-failing-red.svg)]()"

    with open(os.path.join(REPORTS, filename), "w") as f:
        f.write("# REPORT : {} \n\n".format(tag.replace("_", " ")))

        for pkg, files in dic.items():
            f.write("# ``{}`` package\n\n".format(pkg))
            if len(files) > 0:
                f.write(failing_url.format(tag) + "\n\n")
                f.write("The following files have headers which are not in the "
                        "YAML format: \n\n")
                for file in files:
                    f.write("- ``{}``\n".format(file))
            else:
                f.write(passing_url.format(tag) + "\n\n")
                f.write("All ASCII file headers are in the YAML format\n\n")
            f.write("\n\n")


def test_all_ascii_files_readable_by_astropy_io_ascii():

    tbl_failed_dict = {}
    meta_failed_dict = {}
    colname_failed_dict = {}

    for pkg in PKGS_DICT:

        tbl_passed = []
        tbl_failed = []

        meta_passed = []
        meta_failed = []

        colname_passed = []
        colname_failed = []

        test_dir = PKGS_DICT[pkg]["dir"]
        test_files = get_ascii_files_in_package(os.path.join(HOME, test_dir))

        for file in test_files:
            tbl = ioascii.read(file, fast_reader=False)
            print(file)
            if isinstance(tbl, Table):
                tbl_passed += [file]
            else:
                tbl_failed += [file]

            meta = convert_table_comments_to_dict(tbl)
            if isinstance(meta, dict):
                meta_passed += [file]
            else:
                meta_failed += [file]

            if tbl.colnames[0] != "col0":
                colname_passed += [file]
            else:
                colname_failed += [file]

        tbl_failed_dict[pkg] = tbl_failed
        meta_failed_dict[pkg] = meta_failed
        colname_failed_dict[pkg] = colname_failed

    write_report("failed_ascii_table.md", tbl_failed_dict, "ASCII_table_format")
    write_report("failed_ascii_meta.md", meta_failed_dict, "ASCII_meta_format")
    write_report("failed_ascii_colnames.md", meta_failed_dict, "ASCII_colnames")

    print("Tables failing to be read")
    print(tbl_failed_dict)
    print("Meta data failing to be read")
    print(meta_failed_dict)
    print("Table column names failing to be read")
    print(colname_failed_dict)

    for pkg in tbl_failed_dict:
        assert len(tbl_failed_dict[pkg]) == 0

    for pkg in meta_failed_dict:
        assert len(meta_failed_dict[pkg]) == 0
