#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for irdb.badges
"""

from io import StringIO
from unittest import mock

import yaml
import pytest

from irdb.badges import BadgeReport, Badge, BoolBadge, NumBadge, StrBadge, \
    MsgOnlyBadge
from irdb.system_dict import SystemDict


@pytest.fixture(name="temp_dir", scope="module")
def fixture_temp_dir(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("PKG_DIR")
    (tmpdir / "_REPORTS").mkdir()
    return tmpdir


class TestBadgeSubclasses:
    def test_bool(self):
        assert isinstance(Badge("bogus", True), BoolBadge)
        assert isinstance(Badge("bogus", False), BoolBadge)

    def test_num(self):
        assert isinstance(Badge("bogus", 7), NumBadge)
        assert isinstance(Badge("bogus", 3.14), NumBadge)

    def test_str(self):
        assert isinstance(Badge("bogus", "foo"), StrBadge)

    def test_msgonly(self):
        assert isinstance(Badge("bogus", "!foo"), MsgOnlyBadge)


class TestColours:
    @pytest.mark.parametrize("value, colour", [
        ("observation", "blueviolet"),
        ("support", "deepskyblue"),
        ("error", "red"),
        ("missing", "red"),
        ("warning", "orange"),
        ("conflict", "orange"),
        ("incomplete", "orange"),
        ("ok", "green"),
        ("found", "green"),
        ("not_found", "red"),
        ("none", "yellowgreen"),
    ])
    def test_special_strings(self, value, colour):
        assert Badge("bogus", value).colour == colour

    def test_bool(self):
        assert Badge("bogus", True).colour == "green"
        assert Badge("bogus", False).colour == "red"

    def test_num(self):
        assert Badge("bogus", 7).colour == "lightblue"


class TestPattern:
    def test_simple(self):
        with StringIO() as str_stream:
            Badge("bogus", "Error").write(str_stream)
            pattern = "[![](https://img.shields.io/badge/bogus-Error-red)]()"
            assert pattern in str_stream.getvalue()

    def test_msg_only(self):
        with StringIO() as str_stream:
            Badge("bogus", "!OK").write(str_stream)
            pattern = "[![](https://img.shields.io/badge/bogus-green)]()"
            assert pattern in str_stream.getvalue()


class TestSpecialChars:
    def test_space(self):
        badge = Badge("bogus foo", "bar baz")
        assert badge.key == "bogus_foo"
        assert badge.value == "bar_baz"

    def test_dash(self):
        badge = Badge("bogus-foo", "bar-baz")
        assert badge.key == "bogus--foo"
        assert badge.value == "bar--baz"


class TestReport:
    # TODO: the repeated setup stuff should be a fixture or something I guess

    @pytest.mark.usefixtures("temp_dir")
    def test_writes_yaml(self, temp_dir):
        with mock.patch("irdb.badges.PKG_DIR", temp_dir):
            with BadgeReport("test.yaml", "test.md") as report:
                report["!foo.bar"] = "bogus"
            assert (temp_dir / "_REPORTS/test.yaml").exists()

    @pytest.mark.usefixtures("temp_dir")
    def test_writes_md(self, temp_dir):
        with mock.patch("irdb.badges.PKG_DIR", temp_dir):
            with BadgeReport("test.yaml", "test.md") as report:
                report["!foo.bar"] = "bogus"
            assert (temp_dir / "_REPORTS/test.md").exists()

    @pytest.mark.usefixtures("temp_dir")
    def test_yaml_content(self, temp_dir):
        with mock.patch("irdb.badges.PKG_DIR", temp_dir):
            with BadgeReport("test.yaml", "test.md") as report:
                report["!foo.bar"] = "bogus"
            path = temp_dir / "_REPORTS/test.yaml"
            with path.open(encoding="utf-8") as file:
                dic = SystemDict(yaml.full_load(file))
                assert "!foo.bar" in dic
                assert dic["!foo.bar"] == "bogus"

    @pytest.mark.usefixtures("temp_dir")
    def test_md_content(self, temp_dir):
        with mock.patch("irdb.badges.PKG_DIR", temp_dir):
            with BadgeReport("test.yaml", "test.md") as report:
                report["!foo.bar"] = "bogus"
            path = temp_dir / "_REPORTS/test.md"
            markdown = path.read_text(encoding="utf-8")
            assert "## foo" in markdown
            badge = "[![](https://img.shields.io/badge/bar-bogus-lightgrey)]()"
            assert badge in markdown
