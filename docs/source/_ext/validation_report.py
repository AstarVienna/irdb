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
        self.suite = root.find("testsuite")  # only one suit per file supported
        self.name = self.suite.get("name", "N/A")
        self.summary = self._parse_testsuite()

    def __str__(self) -> str:
        """Return str(self)."""
        return f"Validation Report for {self.name}"

    def iter_testcases(self):
        """Iterate over all testcase instances."""
        for testcase in self.suite.findall("testcase"):
            yield self._parse_testcase(testcase)

    def _parse_testsuite(self):
        summary = {
            "errors": int(self.suite.get("errors", -1)),
            "failures": int(self.suite.get("failures", -1)),
            "skipped": int(self.suite.get("skipped", -1)),
            "tests": int(self.suite.get("tests", -1)),
            "time": float(self.suite.get("time", -1.)),  # [s]
        }
        return summary

    def _parse_testcase(self, testcase):
        data = {
            "classname": self._parse_classname(testcase),
            "name": testcase.get("name", "N/A"),
            "time": float(testcase.get("time", -1.)),
            "status": "passed",
            "properties": {},
            "message": "",  # available for skipped and failed tests and errors
            "text": "",  # available for failed tests and errors
        }

        if (error := testcase.find("error")) is not None:
            data["status"] = "error"
            data["message"] = error.get("message")
            data["text"] = error.text
        elif (failure := testcase.find("failure")) is not None:
            data["status"] = "failed"
            data["message"] = failure.get("message")
            data["text"] = failure.text
        elif (skipped := testcase.find("skipped")) is not None:
            status = skipped.get("type").removeprefix("pytest.")
            status = status + "ped" if status == "skip" else status + "ed"
            data["status"] = status
            data["message"] = skipped.get("message")
        # Note: xfail is a type of skip, Xpass looks identical to pass in xml

        if props := testcase.find("properties"):
            for prop in props.findall("property"):
                data["properties"][prop.get("name")] = prop.get("value")

        return data

    def _parse_classname(self, testcase) -> str:
        if (classname := testcase.get("classname")) is None:
            return "N/A"
        return classname.removeprefix(f"{self.name}.").removeprefix("tests.")


class ValidationReportDirective(Directive):
    required_arguments = 1  # path to xml

    headers = {
        "AO mode": None,
        "IMG mode": None,
        "Filter": None,
        "Expected": "mag",
        "Obtained": "mag",
        "Difference": "mag",
        "Status": None,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report = ValidationReport(self.arguments[0])

    def run(self):
        summary = nodes.paragraph(text=(
            f"Showing results from {self.report.summary['tests']} "
            f"tests for {self.report.name}"
        ))

        table = nodes.table()
        tgroup = nodes.tgroup(cols=len(self.headers))
        table += tgroup

        for _ in self.headers:
            tgroup += nodes.colspec(colwidth=1)

        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for header, unit in self.headers.items():
            entry = nodes.entry()
            entry += nodes.Text(header)
            if unit is not None:
                self._add_raw_html(entry, "<br>")
                entry += nodes.Text(f"[{unit}]")
            header_row += entry
        thead += header_row

        tbody = nodes.tbody()
        tgroup += tbody
        tbody.extend(list(self._collect_rows()))

        footnote = nodes.paragraph(text=(
            "Difference is calculated as obtained - expected, meaning a "
            "positive difference indicates ScopeSim reached a fainter limiting "
            "magnitude than the reference document, while a negative difference"
            " means ScopeSim did not reach the reference magnitude in that "
            "combination of modes and filter."
        ))

        return [summary, table, footnote]

    def _collect_rows(self):
        for testcase in self.report.iter_testcases():
            row = nodes.row(classes=[f"pytest-{testcase['status']}"])
            self._add_properties_to_row(row, testcase)

            entry = nodes.entry()
            if (url := testcase["properties"].get("link")) is not None:
                row["classes"].append("clickable-row")
                href_html = (
                    "<a class=\"row-anchor\" "
                    "target=\"_blank\" rel=\"noopener noreferrer\" "
                    f"href=\"../../{url}\">{testcase['status']}</a>"
                )
                self._add_raw_html(entry, href_html)
            else:
                entry += nodes.Text(testcase["status"])
            row += entry

            yield row

    def _add_properties_to_row(self, row, testcase) -> None:
        if not testcase["properties"]:
            return  # skip
        self._add_cell_from_properties(row, testcase, "ao_mode")
        self._add_cell_from_properties(row, testcase, "img_mode")
        self._add_cell_from_properties(row, testcase, "filter")

        entry = nodes.entry(classes=["nowrap"])
        self._add_text_from_properties(entry, testcase, "expected")
        self._add_raw_html(entry, " &plusmn; ")
        self._add_text_from_properties(entry, testcase, "tolerance")
        row += entry

        self._add_cell_from_properties(row, testcase, "obtained")
        self._add_cell_from_properties(row, testcase, "difference")

    def _add_cell_from_properties(self, row, testcase, key: str) -> None:
        entry = nodes.entry(classes=["nowrap"])
        self._add_text_from_properties(entry, testcase, key)
        row += entry

    @staticmethod
    def _add_text_from_properties(entry, testcase, key: str) -> None:
        entry += nodes.Text(testcase["properties"].get(key, ""))

    @staticmethod
    def _add_raw_html(entry, html: str) -> None:
        entry += nodes.raw("", html, format="html")


def setup(app):
    app.add_directive("validation-report", ValidationReportDirective)
