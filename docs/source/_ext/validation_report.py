# -*- coding: utf-8 -*-
"""Custom extension to parse pytest report on validation tests."""
from pathlib import Path
import xml.etree.ElementTree as ET

from docutils import nodes
from docutils.parsers.rst import Directive


class PytestReport:
    def __init__(self, xml_path):
        self.tree = ET.parse(Path(xml_path))
        self.root = self.tree.getroot()

    @property
    def testsuite(self):
        return self.root.find("testsuite")

    def iter_testcases(self):
        for tc in self.testsuite.findall("testcase"):
            yield self._parse_testcase(tc)

    def _parse_testcase(self, tc):
        data = {
            "status": "passed",
            "properties": {},
        }

        if tc.find("failure") is not None:
            data["status"] = "failed"
        elif tc.find("skipped") is not None:
            data["status"] = "skipped"

        props = tc.find("properties")
        if props is not None:
            for prop in props.findall("property"):
                name = prop.attrib.get("name")
                value = prop.attrib.get("value")
                data["properties"][name] = value

        return data


class PytestReportDirective(Directive):
    required_arguments = 1  # path to xml

    def run(self):
        report = PytestReport(self.arguments[0])

        headers = ["AO mode", "IMG mode", "Filter", "Expected", "Obtained", "Difference", "Status"]

        table = nodes.table()
        tgroup = nodes.tgroup(cols=len(headers))
        table += tgroup

        for _ in headers:
            tgroup += nodes.colspec(colwidth=1)

        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for h in headers:
            entry = nodes.entry()
            entry += nodes.paragraph(text=h)
            header_row += entry
        thead += header_row

        tbody = nodes.tbody()
        tgroup += tbody

        for tc in report.iter_testcases():
            props = tc["properties"]

            row = nodes.row(classes=[f"pytest-{tc['status']}"])

            values = [
                props.get("filter", ""),
                props.get("ao_mode", ""),
                props.get("img_mode", ""),
                f"{props.get('expected', '')} mag",
                f"{props.get('obtained', '')} mag",
                f"{props.get('difference', '')} mag",
                tc["status"],
            ]

            for v in values:
                entry = nodes.entry()
                entry += nodes.paragraph(text=str(v))
                row += entry

            tbody += row

        return [table]


def setup(app):
    app.add_directive("pytest-report", PytestReportDirective)
