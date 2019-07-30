import os
from os import path as pth

from tests.utils import load_badge_yaml, write_badge_yaml, make_badge_report
from tests.system_dict import SystemDict


class TestMakeBadgeReport:
    """
    Run this to make a Badge report

    Run test_package_contents before running this test
    """
    def test_reads_yaml_correctly(self):
        # if not pth.exists("../_REPORTS/badges.yaml"):
        #     with open(pth.join(pth.dirname(__file__),
        #                        "../_REPORTS/badges.yaml"), "w") as f:
        #         f.write("")

        print(make_badge_report())


class TestLoadBadgeYaml:
    def test_reads_in_badge_yaml(self):
        badges = load_badge_yaml()

        assert isinstance(badges, SystemDict)
        assert len(badges.dic) > 0

        print(badges)


class TestWriteBadgeYaml:
    def test_write_badge_yaml_contents_to_file(self):
        fname = "new_badges.yaml"
        badges = load_badge_yaml()
        write_badge_yaml(badges, fname)
        new_badges = load_badge_yaml(fname)

        for key in badges.dic:
            assert badges[key] == new_badges[key]

        dname = pth.join(pth.dirname(__file__), "../", "_REPORTS")
        os.remove(pth.join(dname, fname))
