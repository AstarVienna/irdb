"""Conftest for MAVIS tests."""

from pathlib import Path
from datetime import datetime

import numpy as np
import pytest

DOCS_DIR = Path(__file__).parent.parent / "docs"
TESTS_DIR = Path(__file__).parent


class RadiometryReport:
    """Accumulates results from radiometry tests and writes the report."""

    def __init__(self):
        self.throughput = {}
        self.lim_mag = {}
        self.background = {}
        self.star_field = {}

    def write(self):
        """Generate the full report with plots."""
        DOCS_DIR.mkdir(exist_ok=True)

        try:
            import matplotlib
            matplotlib.use("Agg")
            from matplotlib import pyplot as plt
        except ImportError:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        sections = []
        sections.append("# MAVIS Radiometry Report\n\n")
        sections.append(f"Auto-generated on **{timestamp}** by "
                        "`pytest MAVIS/tests/`\n\n")

        sections.append(
            "MAVIS (MCAO Assisted Visible Imager and Spectrograph) is a "
            "next-generation ESO VLT instrument at the Nasmyth A focus of "
            "UT4 (Yepun). It uses an MCAO system to deliver "
            "near-diffraction-limited images in the visible over a "
            "30x30 arcsec field of view.\n\n"
        )
        sections.append(
            "Instrument parameters, the filter list and known limitations are "
            "documented in [README.md](README.md); the underlying "
            "specifications and their sources are in "
            "[../background_info/mavis_baseline_specification.md]"
            "(../background_info/mavis_baseline_specification.md). "
            "This file holds only the numbers measured by the test suite.\n\n"
        )
        sections.append(
            "**Note:** the PSF in this package is a placeholder Gaussian and "
            "the filter curves are top-hat approximations. This report is a "
            "consistency check, not a science-grade performance "
            "prediction.\n\n"
        )

        if self.throughput:
            self._plot_throughput(plt, sections)

        if self.star_field:
            self._plot_star_field(plt, sections)

        if self.lim_mag:
            self._plot_limiting_magnitudes(plt, sections)

        if not self.lim_mag and not self.background and not self.throughput:
            sections.append(
                "*No radiometry data collected. Run slow tests with "
                "`pytest MAVIS/tests/ -m slow` to include radiometry tests.*\n"
            )

        report_path = DOCS_DIR / "radiometry_report.md"
        report_path.write_text("".join(sections), encoding="utf-8")

    def _plot_throughput(self, plt, sections):
        fig, ax = plt.subplots(figsize=(8, 5))
        for filt, (wave, tc) in sorted(self.throughput.items()):
            ax.plot(wave * 1000, tc, label=filt, linewidth=1.2)
        ax.set_xlabel("Wavelength [nm]")
        ax.set_ylabel("System throughput")
        ax.set_title("MAVIS imager system throughput (no atmosphere)")
        ax.legend(ncol=3, fontsize=8)
        ax.set_xlim(300, 1050)
        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(DOCS_DIR / "throughput.png", dpi=150)
        plt.close(fig)

        sections.append("## System Throughput\n\n")
        sections.append("![System throughput](throughput.png)\n\n")
        sections.append(
            "System throughput per filter (VLT mirrors + AO module + "
            "filter + detector QE, **no atmosphere**).\n\n"
        )

    def _plot_star_field(self, plt, sections):
        n = len(self.star_field)
        fig, axes = plt.subplots(1, n, figsize=(5 * n + 1, 5))
        if n == 1:
            axes = [axes]
        for ax, (filt, data) in zip(axes, sorted(self.star_field.items())):
            img = data["image"]
            med = np.median(img[20:-20, 20:-20])
            std = np.std(img[20:-20, 20:-20])
            vmin = max(med - std, 1)
            vmax = med + 10 * std
            ax.imshow(img, origin="lower", cmap="inferno",
                      vmin=vmin, vmax=vmax, norm="log")
            ax.set_title(f"{filt}-band readout")
            ax.set_xlabel("pixel")
            ax.set_ylabel("pixel")
        fig.suptitle(
            "MAVIS imager detector readout -- star field",
            fontsize=11,
        )
        fig.tight_layout()
        fig.savefig(DOCS_DIR / "star_field_image.png", dpi=150)
        plt.close(fig)

        sections.append("## Star Field Image\n\n")
        sections.append("![Star field image](star_field_image.png)\n\n")

    def _plot_limiting_magnitudes(self, plt, sections):
        n = len(self.lim_mag)
        fig, axes = plt.subplots(1, n, figsize=(5 * n + 1, 5))
        if n == 1:
            axes = [axes]
        for ax, (filt, data) in zip(axes, sorted(self.lim_mag.items())):
            mags = data["mags"]
            snrs = data["snrs"]
            pos = snrs > 0
            ax.scatter(mags[pos], snrs[pos], s=10, alpha=0.4, color="#4C72B0")
            ax.axhline(5, color="gray", linestyle=":", label="S/N = 5")
            ax.set_yscale("log")
            ax.set_xlabel("AB magnitude")
            ax.set_ylabel("S/N")
            ax.set_title(f"{filt}-band")
            ax.legend(fontsize=7)
            ax.grid(True, alpha=0.3, which="both")
        fig.suptitle("MAVIS imager limiting magnitudes", fontsize=11)
        fig.tight_layout()
        fig.savefig(DOCS_DIR / "limiting_magnitudes.png", dpi=150)
        plt.close(fig)

        sections.append("## Limiting Magnitudes\n\n")
        sections.append("![Limiting magnitudes](limiting_magnitudes.png)\n\n")


_report = RadiometryReport()


@pytest.fixture(scope="session")
def report():
    return _report


def pytest_sessionfinish(session, exitstatus):
    _report.write()
