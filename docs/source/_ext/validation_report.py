# -*- coding: utf-8 -*-
"""Custom extension to parse pytest report on validation tests."""

from pathlib import Path
import xml.etree.ElementTree as ET

from docutils import nodes
from docutils.parsers.rst import Directive


class PytestReport:
    def __init__(self, xml_path):
        self.xml_path = Path(xml_path)
        self.tree = ET.parse(self.xml_path)
        self.root = self.tree.getroot()

    @property
    def testsuite(self):
        return self.root.find("testsuite")

    @property
    def summary(self):
        ts = self.testsuite
        return {
            "tests": int(ts.attrib.get("tests", 0)),
            "failures": int(ts.attrib.get("failures", 0)),
            "errors": int(ts.attrib.get("errors", 0)),
            "skipped": int(ts.attrib.get("skipped", 0)),
            "time": float(ts.attrib.get("time", 0.0)),
        }

    def iter_testcases(self):
        for tc in self.testsuite.findall("testcase"):
            yield self._parse_testcase(tc)

    def _parse_testcase(self, tc):
        data = {
            "classname": tc.attrib.get("classname"),
            "name": tc.attrib.get("name"),
            "time": float(tc.attrib.get("time", 0.0)),
            "status": "passed",
            "properties": {},
        }

        # Status detection
        if tc.find("failure") is not None:
            data["status"] = "failed"
            data["failure_message"] = tc.find("failure").attrib.get("message")
        elif tc.find("skipped") is not None:
            data["status"] = "skipped"

        # Properties
        props = tc.find("properties")
        if props is not None:
            for prop in props.findall("property"):
                name = prop.attrib.get("name")
                value = prop.attrib.get("value")
                data["properties"].setdefault(name, []).append(value)

        return data


class PytestReportDirective(Directive):
    required_arguments = 1  # path to xml

    def run(self):
        xml_path = self.arguments[0]
        report = PytestReport(xml_path)

        summary = report.summary

        content = []
        content.append(f"**Total tests:** {summary['tests']}")
        content.append(f"**Failures:** {summary['failures']}")
        content.append(f"**Skipped:** {summary['skipped']}")
        content.append("")

        for tc in report.iter_testcases():
            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⚠️",
            }[tc["status"]]

            content.append(
                f"- {status_icon} `{tc['name']}` "
                f"({tc['properties'].get('filter', [''])[0]})"
            )

        paragraph = nodes.paragraph(text="\n".join(content))
        return [paragraph]


def setup(app):
    app.add_directive("pytest-report", PytestReportDirective)
