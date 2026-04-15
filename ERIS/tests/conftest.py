"""Conftest for ERIS tests.

Provides the ``report`` fixture that collects radiometry results and
generates a Markdown report with plots in ``ERIS/docs/`` after
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
        self.throughput = {}      # {mode_filter: (wave, tc)}
        self.lim_mag = {}         # {filter: {eso, scopesim, mags, snrs, ...}}
        self.background = {}      # {filter: measured_bg}
        self.star_field = {}      # {filter: {image, bg_rate}}

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
        sections.append("# ERIS NIX Radiometry Report\n\n")
        sections.append(f"Auto-generated on **{timestamp}** by "
                        "`pytest ERIS/tests/`\n\n")
        sections.append(
            "Source code: "
            "[test_eris_nix.py](../tests/test_eris_nix.py) "
            "| [conftest.py](../tests/conftest.py)\n\n"
        )

        # ---- Instrument overview ----
        sections.append("## Instrument Overview\n\n")
        sections.append(
            "ERIS (Enhanced Resolution Imager and Spectrograph) is a "
            "Cassegrain AO instrument on VLT UT4 combining the NIX imager "
            "(1-5 um) with the SPIFFIER IFU spectrograph (1-2.5 um).\n\n"
        )
        sections.append(
            "Reference: [Davies et al. 2023, A&A 674, A207]"
            "(https://doi.org/10.1051/0004-6361/202346559), "
            "[ERIS User Manual v117.1]"
            "(https://www.eso.org/sci/facilities/paranal/instruments/"
            "eris/doc.html)\n\n"
        )
        sections.append("### NIX Parameters\n\n")
        sections.append("| Parameter | Value |\n")
        sections.append("|-----------|-------|\n")
        sections.append("| Pixel scales | 13 mas/pix (JHK, LM), "
                        "27 mas/pix (JHK) |\n")
        sections.append("| Field of view | 26.4\" (13mas), "
                        "55.4\" (27mas) |\n")
        sections.append("| Detector | 1x Hawaii-2RG (2048x2048), "
                        "5 um cutoff |\n")
        sections.append("| Wavelength range | 1 - 5 um |\n")
        sections.append("| Read noise (slow) | 9 e- (60s DIT) |\n")
        sections.append("| Dark current (35K) | 0.10 e-/s/pixel |\n")
        sections.append("| Well depth | 85,000 e- |\n")
        sections.append("| AO modes | NGS, LGS, SE, No-AO |\n\n")

        sections.append("### Measured Total Throughput (Davies+2023)\n\n")
        sections.append(
            "Including telescope + atmosphere + instrument + QE:\n\n"
        )
        sections.append(
            "| Band | Total Throughput | Instrument Only |\n"
        )
        sections.append(
            "|------|----------------:|----------------:|\n"
        )
        sections.append("| J    |            42%  |         70-75%  |\n")
        sections.append("| H    |            61%  |         70-75%  |\n")
        sections.append("| K    |            52%  |         70-75%  |\n")
        sections.append("| L/M  |              -- |         65-70%  |\n\n")

        # ---- System throughput plot ----
        if self.throughput:
            self._plot_throughput(plt, sections)

        # ---- Star field images ----
        if self.star_field:
            self._plot_star_field(plt, sections)

        # ---- Limiting magnitude plots ----
        if self.lim_mag:
            self._plot_limiting_magnitudes(plt, sections)

        # ---- Sky background ----
        if self.background:
            self._plot_sky_background(plt, sections)

        # ---- Noise budget ----
        if self.lim_mag:
            self._write_noise_budget(sections)

        if (not self.lim_mag and not self.background
                and not self.throughput):
            sections.append(
                "*No radiometry data collected. Run slow tests with "
                "`pytest ERIS/tests/ -m slow` to include "
                "radiometry tests.*\n"
            )

        report_path = DOCS_DIR / "radiometry_report.md"
        report_path.write_text("".join(sections), encoding="utf-8")

    # ------------------------------------------------------------------
    # Plot helpers
    # ------------------------------------------------------------------

    def _plot_throughput(self, plt, sections):
        """System throughput per filter, grouped by wavelength regime."""
        jhk_filters = ["J", "H", "Ks", "Pa-b", "Fe-II", "H2-cont",
                        "H2-1-0S", "Br-g", "K-peak", "IB-2.42", "IB-2.48"]
        lm_filters = ["Short-Lp", "Lp", "L-Broad", "Mp",
                       "Br-a-cont", "Br-a"]

        # Separate JHK and LM throughputs
        jhk_data = {k: v for k, v in self.throughput.items()
                    if k in jhk_filters}
        lm_data = {k: v for k, v in self.throughput.items()
                   if k in lm_filters}

        n_panels = (1 if jhk_data else 0) + (1 if lm_data else 0)
        if n_panels == 0:
            return

        fig, axes = plt.subplots(1, max(n_panels, 1),
                                 figsize=(7 * n_panels, 5))
        if n_panels == 1:
            axes = [axes]

        idx = 0
        if jhk_data:
            ax = axes[idx]
            for filt, (wave, tc) in sorted(jhk_data.items()):
                ax.plot(wave, tc, label=filt, linewidth=1.2)
            ax.set_xlabel("Wavelength [um]")
            ax.set_ylabel("System throughput")
            ax.set_title("NIX JHK system throughput (no atmosphere)")
            ax.legend(ncol=3, fontsize=7)
            ax.set_xlim(0.8, 2.6)
            ax.set_ylim(bottom=0)
            ax.grid(True, alpha=0.3)
            idx += 1

        if lm_data:
            ax = axes[idx]
            for filt, (wave, tc) in sorted(lm_data.items()):
                ax.plot(wave, tc, label=filt, linewidth=1.2)
            ax.set_xlabel("Wavelength [um]")
            ax.set_ylabel("System throughput")
            ax.set_title("NIX LM system throughput (no atmosphere)")
            ax.legend(ncol=2, fontsize=7)
            ax.set_xlim(2.5, 5.5)
            ax.set_ylim(bottom=0)
            ax.grid(True, alpha=0.3)

        fig.tight_layout()
        fig.savefig(DOCS_DIR / "throughput.png", dpi=150)
        plt.close(fig)

        sections.append("## System Throughput\n\n")
        sections.append("![System throughput](throughput.png)\n\n")
        sections.append(
            "System throughput per filter (VLT mirrors + ERIS warm optics "
            "+ NIX camera optics + filter + detector QE, "
            "**no atmosphere**).\n\n"
        )

    def _plot_star_field(self, plt, sections):
        """Detector readout frames per filter."""
        n = len(self.star_field)
        fig, axes = plt.subplots(1, n, figsize=(5 * n + 1, 5))
        if n == 1:
            axes = [axes]
        for ax, (filt, data) in zip(axes, sorted(self.star_field.items())):
            img = data["image"]
            med = np.median(img[20:-20, 20:-20])
            std = np.std(img[20:-20, 20:-20])
            vmin = max(med - 1 * std, 1)
            vmax = med + 10 * std
            ax.imshow(img, origin="lower", cmap="inferno",
                      vmin=vmin, vmax=vmax, norm="log")
            ax.set_title(f"{filt}-band readout")
            ax.set_xlabel("pixel")
            ax.set_ylabel("pixel")
        fig.suptitle(
            "ERIS NIX detector readout -- star field "
            "(DIT=3600s, NGS AO, 13mas/pix)",
            fontsize=11,
        )
        fig.tight_layout()
        fig.savefig(DOCS_DIR / "star_field_image.png", dpi=150)
        plt.close(fig)

        sections.append("## Star Field Image\n\n")
        sections.append("![Star field image](star_field_image.png)\n\n")
        sections.append(
            "Detector readout frame (DIT=3600s) from the NIX H2RG, "
            "showing a star grid covering the 26.4\" FoV. "
            "Log colour scale.\n\n"
        )

        sections.append("### Generating a star field observation\n\n")
        sections.append("```python\n")
        sections.append("import scopesim\n")
        sections.append("from scopesim.source import source_templates "
                        "as st\n\n")
        sections.append(
            'scopesim.rc.__config__["!SIM.file.local_packages_path"]'
            ' = "/path/to/irdb"\n\n'
        )
        sections.append("cmd = scopesim.UserCommands(\n")
        sections.append('    use_instrument="ERIS",\n')
        sections.append("    properties={\n")
        sections.append('        "!OBS.modes": ["NGS", "nixIMG_JHK13"],\n')
        sections.append('        "!OBS.filter_name": "Ks",\n')
        sections.append('        "!OBS.dit": 3600,\n')
        sections.append("    },\n")
        sections.append(")\n")
        sections.append("opt = scopesim.OpticalTrain(cmd)\n\n")
        sections.append(
            "src = st.star_field(n=100, mmin=15, mmax=25, "
            "width=26, use_grid=True)\n"
        )
        sections.append("opt.observe(src)\n")
        sections.append("hdus = opt.readout()\n")
        sections.append("```\n\n")

    def _plot_limiting_magnitudes(self, plt, sections):
        """S/N scatter + linear fit + reference lines per filter."""
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

            pos = snrs > 0
            ax.scatter(mags[pos], snrs[pos], s=10, alpha=0.4,
                       color="#4C72B0", zorder=3,
                       label="Aperture photometry")

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
            "ERIS NIX limiting magnitudes\n"
            "(S/N=5, point source, 3600s, NGS AO, airmass 1.2)",
            fontsize=11,
        )
        fig.tight_layout()
        fig.savefig(DOCS_DIR / "limiting_magnitudes.png", dpi=150)
        plt.close(fig)

        sections.append("## Limiting Magnitudes\n\n")
        sections.append(
            "![Limiting magnitudes](limiting_magnitudes.png)\n\n"
        )
        sections.append(
            "Blue scatter points show S/N measured from the noisy "
            "detector readout frame via aperture photometry "
            "(signal in 9x9 pixel box, noise from std in annulus "
            "r=10-15 pixels). "
            "The black line is a linear fit to log(S/N) vs magnitude.\n\n"
        )

        sections.append(
            "| Filter | ESO [Vega] | ScopeSim [Vega] | Delta |\n"
        )
        sections.append(
            "|--------|----------:|-----------:|------:|\n"
        )
        for filt in sorted(self.lim_mag):
            d = self.lim_mag[filt]
            delta = d["scopesim_lim_mag"] - d["eso_lim_mag"]
            sections.append(
                f"| {filt:6s} | {d['eso_lim_mag']:8.1f} | "
                f"{d['scopesim_lim_mag']:9.1f} | {delta:+5.1f} |\n"
            )
        sections.append("\n")
        sections.append(
            "ESO reference: point source, S/N=5, DIT=3600s, "
            "0.8\" seeing, airmass 1.2. "
            "Values from ERIS ETC.\n\n"
        )

    def _plot_sky_background(self, plt, sections):
        """Bar chart of sky background rates."""
        fig, ax = plt.subplots(figsize=(6, 4))
        filters = sorted(self.background.keys())
        bg_vals = [self.background[f] for f in filters]
        colors = {"J": "#4C72B0", "H": "#55A868", "Ks": "#C44E52"}
        bar_colors = [colors.get(f, "#888888") for f in filters]
        bars = ax.bar(filters, bg_vals, color=bar_colors)
        ax.set_ylabel("Sky background [e-/s/pixel]")
        ax.set_title("ERIS NIX sky background (airmass=1.2, pwv=2.5)")
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

    def _write_noise_budget(self, sections):
        """Noise budget table at limiting magnitude."""
        sections.append("## Noise Budget\n\n")
        sections.append(
            "| Filter | Sky BG [e-/s/pix] | Dark [e-/s/pix] "
            "| Read noise [e-] |\n"
        )
        sections.append(
            "|--------|------------------:|----------------:"
            "|----------------:|\n"
        )
        for filt in sorted(self.lim_mag):
            d = self.lim_mag[filt]
            sections.append(
                f"| {filt:6s} | {d['bg_rate']:15.1f} | "
                f"{'0.10':>14s} | {'12':>14s} |\n"
            )
        sections.append("\n")


# Module-level singleton so all tests share it
_report = RadiometryReport()


@pytest.fixture(scope="session")
def report():
    """Session-scoped fixture providing the shared report collector."""
    return _report


def pytest_sessionfinish(session, exitstatus):
    """Write the radiometry report after all tests complete."""
    _report.write()
