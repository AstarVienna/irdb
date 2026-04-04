"""Conftest for HAWKI_new tests.

Provides the ``report`` fixture that collects radiometry results and
generates a Markdown report with plots in ``HAWKI_new/docs/`` after
the test session finishes.
"""

from pathlib import Path
from datetime import datetime

import numpy as np
import pytest

DOCS_DIR = Path(__file__).parent.parent / "docs"
TESTS_DIR = Path(__file__).parent


class RadiometryReport:
    """Accumulates results from radiometry tests and writes the report."""

    def __init__(self):
        self.throughput = {}      # {filter: (wave, tc)}
        self.lim_mag = {}         # {filter: {eso, scopesim, bg_rate, ...}}
        self.background = {}      # {filter: measured_bg}
        self.star_field = {}      # {filter: {mags, snrs, image, bg_rate}}

    def write(self):
        """Generate the full report with plots."""
        DOCS_DIR.mkdir(exist_ok=True)

        try:
            import matplotlib
            matplotlib.use("Agg")
            from matplotlib import pyplot as plt
            from matplotlib.colors import LogNorm
        except ImportError:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        sections = []
        sections.append("# HAWKI_new Radiometry Report\n\n")
        sections.append(f"Auto-generated on **{timestamp}** by "
                        "`pytest HAWKI_new/tests/`\n\n")
        sections.append(
            "Source code: "
            "[test_hawki_new.py](../tests/test_hawki_new.py) "
            "| [conftest.py](../tests/conftest.py)\n\n"
        )

        # ---- ESO Reference Values ----
        sections.append("## ESO Reference Values\n\n")
        sections.append(
            "Reference: [ESO HAWK-I Overview]"
            "(https://www.eso.org/sci/facilities/paranal/instruments/"
            "hawki/overview.html), "
            "[HAWK-I User Manual v116.2]"
            "(https://www.eso.org/sci/facilities/paranal/instruments/"
            "hawki/doc.html)\n\n"
        )
        sections.append("### Instrument Parameters\n\n")
        sections.append("| Parameter | Value |\n")
        sections.append("|-----------|-------|\n")
        sections.append("| Field of view | 7.5' x 7.5' |\n")
        sections.append("| Pixel scale | 0.1064 arcsec/pixel |\n")
        sections.append("| Detectors | 4x Hawaii-2RG (2048x2048) |\n")
        sections.append("| Wavelength range | 0.9 - 2.5 um |\n")
        sections.append("| Read noise (DIT > 15s) | ~5 e- |\n")
        sections.append("| Dark current (75K) | 0.10 - 0.15 e-/s/pixel |\n")
        sections.append("| Linear range | 60,000 e- |\n\n")

        sections.append("### ESO Limiting Magnitudes\n\n")
        sections.append(
            "S/N = 5 on a point source, 3600s integration, "
            "0.8\" seeing, airmass 1.2:\n\n"
        )
        sections.append(
            "| Filter | Limiting mag [Vega] | Limiting mag [AB] |\n"
        )
        sections.append(
            "|--------|--------------------:|------------------:|\n"
        )
        sections.append("| J      |               23.9 |              24.8 |\n")
        sections.append("| H      |               22.5 |              23.9 |\n")
        sections.append("| Ks     |               22.3 |              24.2 |\n")
        sections.append("\n")

        # ---- System throughput plot ----
        if self.throughput:
            fig, ax = plt.subplots(figsize=(10, 5))
            for filt, (wave, tc) in sorted(self.throughput.items()):
                ax.plot(wave, tc, label=filt)
            ax.set_xlabel("Wavelength [um]")
            ax.set_ylabel("System throughput")
            ax.set_title("HAWKI_new system throughput (atmosphere excluded)")
            ax.legend(ncol=3, fontsize=8)
            ax.set_xlim(0.8, 2.6)
            ax.set_ylim(bottom=0)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            fig.savefig(DOCS_DIR / "throughput.png", dpi=150)
            plt.close(fig)

            sections.append("## System Throughput\n\n")
            sections.append("![System throughput](throughput.png)\n\n")
            sections.append(
                "System throughput per filter (VLT mirrors + HAWKI optics "
                "+ filter + detector QE, **no atmosphere**).\n\n"
            )

        # ---- Star field images (detector readout frames) ----
        if self.star_field:
            n = len(self.star_field)
            fig, axes = plt.subplots(1, n, figsize=(5 * n + 1, 5))
            if n == 1:
                axes = [axes]
            for ax, (filt, data) in zip(axes, sorted(self.star_field.items())):
                img = data["image"]
                med = np.median(img[20:-20, 20:-20])
                std = np.std(img[20:-20, 20:-20])
                vmin = med - 1 * std
                vmax = med + 10 * std
                ax.imshow(img, origin="lower", cmap="inferno",
                          vmin=vmin, vmax=vmax, norm="log")
                ax.set_title(f"{filt}-band readout")
                ax.set_xlabel("pixel")
                ax.set_ylabel("pixel")
            fig.suptitle(
                "HAWKI_new detector readout — star field "
                "(median +/- 10 sigma)",
                fontsize=12,
            )
            fig.tight_layout()
            fig.savefig(DOCS_DIR / "star_field_image.png", dpi=150)
            plt.close(fig)

            sections.append("## Star Field Image\n\n")
            sections.append("![Star field image](star_field_image.png)\n\n")
            sections.append(
                "Detector readout frame (DIT=3600s) from one quadrant of "
                "the H2RG mosaic, showing a 15x15 star grid (mag 15-25) "
                "covering the full focal plane. Log colour scale with "
                "vmin/vmax tuned to reveal faint sources near the "
                "detection limit.\n\n"
            )

            sections.append("### Generating a star field observation\n\n")
            sections.append("```python\n")
            sections.append("import scopesim\n")
            sections.append("from scopesim.source import source_templates as st\n\n")
            sections.append(
                'scopesim.rc.__config__["!SIM.file.local_packages_path"]'
                ' = "/path/to/irdb"\n\n'
            )
            sections.append("cmd = scopesim.UserCommands(\n")
            sections.append('    use_instrument="HAWKI_new",\n')
            sections.append("    properties={\n")
            sections.append('        "!OBS.filter_name": "Ks",\n')
            sections.append('        "!OBS.dit": 3600,\n')
            sections.append('        "!OBS.ndit": 1,\n')
            sections.append("    },\n")
            sections.append(")\n")
            sections.append("opt = scopesim.OpticalTrain(cmd)\n\n")
            sections.append(
                "src = st.star_field(n=225, mmin=15, mmax=25, "
                "width=360, use_grid=True)\n"
            )
            sections.append("opt.observe(src)\n")
            sections.append("hdus = opt.readout()  # 4x H2RG detector images\n")
            sections.append("```\n\n")

        # ---- Limiting magnitude plots (scatter + fit) ----
        if self.lim_mag:
            n = len(self.lim_mag)
            fig, axes = plt.subplots(1, n, figsize=(5 * n + 1, 5))
            if n == 1:
                axes = [axes]

            for ax, (filt, data) in zip(axes, sorted(self.lim_mag.items())):
                mags = data["mags"]
                snrs = data["snrs"]
                eso = data["eso_lim_mag"]
                ss = data["scopesim_lim_mag"]
                snr_limit = 5

                # Scatter: measured S/N from readout aperture photometry
                pos = snrs > 0
                ax.scatter(mags[pos], snrs[pos], s=10, alpha=0.4,
                           color="#4C72B0", zorder=3,
                           label="Aperture photometry")

                # Fitted line through the measurements
                if "fit_slope" in data:
                    fit_mags = np.linspace(mags.min(), mags.max(), 200)
                    fit_snrs = 10 ** (data["fit_slope"] * fit_mags +
                                     data["fit_intercept"])
                    ax.plot(fit_mags, fit_snrs, "k-", linewidth=1.5,
                            zorder=4, label="Linear fit (log S/N)")

                ax.axhline(snr_limit, color="gray", linestyle=":",
                           alpha=0.7, label=f"S/N = {snr_limit}")
                ax.axvline(eso, color="#C44E52", linestyle="--", alpha=0.8,
                           linewidth=2,
                           label=f"ESO lim. = {eso:.1f}")
                ax.axvline(ss, color="#4C72B0", linestyle="--", alpha=0.8,
                           linewidth=2,
                           label=f"ScopeSim = {ss:.1f}")

                ax.set_yscale("log")
                ax.set_xlabel("Vega magnitude")
                ax.set_ylabel("S/N")
                ax.set_title(f"{filt}-band")
                ax.legend(fontsize=7, loc="upper right")
                ax.set_ylim(0.5, 2e4)
                ax.grid(True, alpha=0.3, which="both")

            fig.suptitle(
                "HAWKI_new limiting magnitudes\n"
                "(S/N=5, point source, 3600s, 0.8\" seeing, airmass 1.2)",
                fontsize=11,
            )
            fig.tight_layout()
            fig.savefig(DOCS_DIR / "limiting_magnitudes.png", dpi=150)
            plt.close(fig)

            sections.append("## Limiting Magnitudes\n\n")
            sections.append("![Limiting magnitudes](limiting_magnitudes.png)\n\n")
            sections.append(
                "Blue scatter points show S/N measured from the noisy "
                "detector readout frames via aperture photometry "
                "(signal in 9x9 pixel box, noise from std in annulus "
                "r=10-15 pixels). "
                "The black line is a linear fit to log(S/N) vs magnitude. "
                "Stars below S/N~1 are lost in the noise.\n\n"
            )

            sections.append(
                "| Filter | ESO [Vega] | ScopeSim [Vega] | Delta "
                "| ESO [AB] |\n"
            )
            sections.append(
                "|--------|----------:|-----------:|------:"
                "|---------:|\n"
            )
            eso_ab = {"J": 24.8, "H": 23.9, "Ks": 24.2}
            for filt in sorted(self.lim_mag):
                d = self.lim_mag[filt]
                delta = d["scopesim_lim_mag"] - d["eso_lim_mag"]
                ab = eso_ab.get(filt, "")
                sections.append(
                    f"| {filt:6s} | {d['eso_lim_mag']:8.1f} | "
                    f"{d['scopesim_lim_mag']:9.1f} | {delta:+5.1f} "
                    f"| {ab:>8} |\n"
                )
            sections.append("\n")

        # ---- Background plot ----
        if self.background:
            fig, ax = plt.subplots(figsize=(6, 4))
            filters = sorted(self.background.keys())
            bg_vals = [self.background[f] for f in filters]
            colors = {"J": "#4C72B0", "H": "#55A868", "Ks": "#C44E52"}
            bar_colors = [colors.get(f, "#888888") for f in filters]
            bars = ax.bar(filters, bg_vals, color=bar_colors)
            ax.set_ylabel("Sky background [e-/s/pixel]")
            ax.set_title("HAWKI_new sky background (airmass=1.2, pwv=2.5)")
            ax.grid(True, alpha=0.3, axis="y")
            for bar, val in zip(bars, bg_vals):
                ax.text(bar.get_x() + bar.get_width() / 2, val + 20,
                        f"{val:.0f}", ha="center", va="bottom", fontsize=9)
            fig.tight_layout()
            fig.savefig(DOCS_DIR / "sky_background.png", dpi=150)
            plt.close(fig)

            sections.append("## Sky Background\n\n")
            sections.append("![Sky background](sky_background.png)\n\n")
            sections.append(
                "Measured sky background rates per pixel at airmass=1.2, "
                "pwv=2.5 mm.\n\n"
            )

        # ---- Noise budget table ----
        if self.lim_mag:
            sections.append("## Noise Budget at Limiting Magnitude\n\n")
            sections.append(
                "| Filter | Sky BG | Star signal (15 mag) | "
                "Dark current | Read noise |\n"
            )
            sections.append(
                "|--------|-------:|---------------------:"
                "|------------:|----------:|\n"
            )
            for filt in sorted(self.lim_mag):
                d = self.lim_mag[filt]
                sections.append(
                    f"| {filt:6s} | {d['bg_rate']:5.0f} e-/s/pix | "
                    f"{d['ref_signal']:18.0f} e-/s | "
                    f"0.10 e-/s/pix | 5 e-/pix |\n"
                )
            sections.append(
                "\nStar signal is the total flux from a 15.0 Vega mag "
                "reference star collected in a 9x9 pixel aperture.\n\n"
            )

        if not self.lim_mag and not self.background and not self.throughput:
            sections.append(
                "*No radiometry data collected. Run slow tests with "
                "`pytest HAWKI_new/tests/ -m slow` to include "
                "radiometry tests.*\n"
            )

        report_path = DOCS_DIR / "radiometry_report.md"
        report_path.write_text("".join(sections), encoding="utf-8")


# Module-level singleton so all tests share it
_report = RadiometryReport()


@pytest.fixture(scope="session")
def report():
    """Session-scoped fixture providing the shared report collector."""
    return _report


def pytest_sessionfinish(session, exitstatus):
    """Write the radiometry report after all tests complete."""
    _report.write()
