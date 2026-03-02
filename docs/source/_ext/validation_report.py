# -*- coding: utf-8 -*-
"""Custom extension to parse pytest report on validation tests."""
from pathlib import Path
import xml.etree.ElementTree as ET

from docutils import nodes
from docutils.parsers.rst import Directive


class ValidationReport:
    """XML Parser for Validation Report from Pytest."""

    def __init__(self, xml_path):
        tree = ET.parse(Path(xml_path))
        root = tree.getroot()
        self.suite = root.find("testsuite")

    def iter_testcases(self):
        for testcase in self.suite.findall("testcase"):
            yield self._parse_testcase(testcase)

    def _parse_testcase(self, testcase):
        data = {
            "status": "passed",
            "properties": {},
        }

        if testcase.find("failure") is not None:
            data["status"] = "failed"
        elif testcase.find("skipped") is not None:
            data["status"] = "skipped"

        props = testcase.find("properties")
        if props is not None:
            for prop in props.findall("property"):
                name = prop.attrib.get("name")
                value = prop.attrib.get("value")
                data["properties"][name] = value

        return data


class PytestReportDirective(Directive):
    required_arguments = 1  # path to xml

    def run(self):
        report = ValidationReport(self.arguments[0])

        headers = ["AO mode", "IMG mode", "Filter", "Expected", "Obtained", "Difference", "Status"]
        units = {"Expected": "mag", "Obtained": "mag", "Difference": "mag"}

        table = nodes.table()
        tgroup = nodes.tgroup(cols=len(headers))
        table += tgroup

        for _ in headers:
            tgroup += nodes.colspec(colwidth=1)

        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for header in headers:
            entry = nodes.entry()
            entry += nodes.Text(header)
            if (unit := units.get(header)) is not None:
                entry += nodes.raw("", "<br>", format="html")
                entry += nodes.Text(f"[{unit}]")
            header_row += entry
        thead += header_row

        tbody = nodes.tbody()
        tgroup += tbody

        for tc in report.iter_testcases():
            props = tc["properties"]

            row = nodes.row(classes=[f"pytest-{tc['status']}"])

            values = [
                props.get("ao_mode", ""),
                props.get("img_mode", ""),
                props.get("filter", ""),
                f"{props.get('expected', '')} +/- {props.get('tolerance', '')}",
                props.get("obtained", ""),
                props.get("difference", ""),
                tc["status"],
            ]

            for v in values:
                entry = nodes.entry(classes=["nowrap"])
                entry += nodes.Text(str(v))
                row += entry

            tbody += row

        return [table]


def setup(app):
    app.add_directive("pytest-report", PytestReportDirective)
