#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for irdb.utils

Does currently not test utils.recursive_filename_search()
"""

from pathlib import Path

import pytest

from irdb.utils import get_packages


@pytest.fixture(name="packages", scope="class")
def fixture_packages():
    return dict(get_packages())


class TestGetPackages:
    @pytest.mark.usefixtures("packages")
    def test_includes_various_packages(self, packages):
        wanted = {"Armazones", "ELT", "METIS", "MICADO", "test_package"}
        assert all(pkg_name in packages.keys() for pkg_name in wanted)

    @pytest.mark.usefixtures("packages")
    def test_doesnt_includes_specials(self, packages):
        wanted = {"irdb", "docs", "_REPORTS", ".github"}
        assert all(pkg_name not in packages.keys() for pkg_name in wanted)

    @pytest.mark.usefixtures("packages")
    def test_values_are_path_objects(self, packages):
        assert isinstance(packages["test_package"], Path)

    @pytest.mark.usefixtures("packages")
    def test_only_includes_dirs(self, packages):
        assert all(path.is_dir() for path in packages.values())
