"""
Same radiometry test suite as test_hawki_new.py, but targeting the
original irdb/HAWKI package.  Generates a separate report in
HAWKI_new/docs/hawki_original/.
"""

from pathlib import Path

import pytest
from pytest import approx

import numpy as np
from astropy import units as u

import scopesim
from scopesim import rc
from scopesim.source import source_templates as st

PATH_HERE = Path(__file__).parent
PATH_IRDB = PATH_HERE.parent.parent
rc.__config__["!SIM.file.local_packages_path"] = str(PATH_IRDB)

INSTRUMENT = "HAWKI"
DOCS_DIR = PATH_HERE.parent / "docs" / "hawki_original"


# ---------------------------------------------------------------------------
# Report collector (standalone, not shared with HAWKI_new conftest)
# ---------------------------------------------------------------------------

class _Report:
    def __init__(self):
        self.throughput = {}
        self.lim_mag = {}
        self.background = {}
        self.star_field = {}

    def write(self):
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            import matplotlib
            matplotlib.use("Agg")
            from matplotlib import pyplot as plt
            from matplotlib.colors import LogNorm
        except ImportError:
            return

        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")

        sec = []
        sec.append(f"# HAWKI (original) Radiometry Report\n\n")
        sec.append(f"Auto-generated on **{ts}** by "
                   "`pytest HAWKI_new/tests/test_hawki_original.py`\n\n")
        sec.append(f"Instrument package: `{INSTRUMENT}`\n\n")
        sec.append(
            "Source code: "
            "[test_hawki_original.py](../../tests/test_hawki_original.py)\n\n"
        )

        # ---- ESO reference ----
        sec.append("## ESO Reference Values\n\n")
        sec.append(
            "S/N = 5 on a point source, 3600s integration, "
            "0.8\" seeing, airmass 1.2:\n\n"
        )
        sec.append("| Filter | ESO [Vega] | ESO [AB] |\n")
        sec.append("|--------|----------:|---------:|\n")
        sec.append("| J      |     23.9 |     24.8 |\n")
        sec.append("| H      |     22.5 |     23.9 |\n")
        sec.append("| Ks     |     22.3 |     24.2 |\n\n")

        # ---- throughput ----
        if self.throughput:
            fig, ax = plt.subplots(figsize=(10, 5))
            for filt, (wave, tc) in sorted(self.throughput.items()):
                ax.plot(wave, tc, label=filt)
            ax.set_xlabel("Wavelength [um]")
            ax.set_ylabel("System throughput")
            ax.set_title(f"{INSTRUMENT} system throughput (no atmosphere)")
            ax.legend(ncol=3, fontsize=8)
            ax.set_xlim(0.8, 2.6)
            ax.set_ylim(bottom=0)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            fig.savefig(DOCS_DIR / "throughput.png", dpi=150)
            plt.close(fig)

            sec.append("## System Throughput\n\n")
            sec.append("![System throughput](throughput.png)\n\n")

        # ---- star field image ----
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
                f"{INSTRUMENT} detector readout — star field", fontsize=12)
            fig.tight_layout()
            fig.savefig(DOCS_DIR / "star_field_image.png", dpi=150)
            plt.close(fig)

            sec.append("## Star Field Image\n\n")
            sec.append("![Star field image](star_field_image.png)\n\n")

        # ---- limiting magnitudes ----
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
                ax.axhline(5, color="gray", linestyle=":", alpha=0.7,
                           label="S/N = 5")
                ax.axvline(eso, color="#C44E52", linestyle="--", alpha=0.8,
                           linewidth=2, label=f"ESO lim. = {eso:.1f}")
                ax.axvline(ss, color="#4C72B0", linestyle="--", alpha=0.8,
                           linewidth=2, label=f"ScopeSim = {ss:.1f}")
                ax.set_yscale("log")
                ax.set_xlabel("Vega magnitude")
                ax.set_ylabel("S/N")
                ax.set_title(f"{filt}-band")
                ax.legend(fontsize=7, loc="upper right")
                ax.set_ylim(0.5, 2e4)
                ax.grid(True, alpha=0.3, which="both")
            fig.suptitle(
                f"{INSTRUMENT} limiting magnitudes\n"
                "(S/N=5, point source, 3600s, 0.8\" seeing, airmass 1.2)",
                fontsize=11)
            fig.tight_layout()
            fig.savefig(DOCS_DIR / "limiting_magnitudes.png", dpi=150)
            plt.close(fig)

            sec.append("## Limiting Magnitudes\n\n")
            sec.append("![Limiting magnitudes](limiting_magnitudes.png)\n\n")
            eso_ab = {"J": 24.8, "H": 23.9, "Ks": 24.2}
            sec.append(
                "| Filter | ESO [Vega] | ScopeSim [Vega] | Delta "
                "| ESO [AB] |\n"
            )
            sec.append(
                "|--------|----------:|-----------:|------:"
                "|---------:|\n"
            )
            for filt in sorted(self.lim_mag):
                d = self.lim_mag[filt]
                delta = d["scopesim_lim_mag"] - d["eso_lim_mag"]
                ab = eso_ab.get(filt, "")
                sec.append(
                    f"| {filt:6s} | {d['eso_lim_mag']:8.1f} | "
                    f"{d['scopesim_lim_mag']:9.1f} | {delta:+5.1f} "
                    f"| {ab:>8} |\n"
                )
            sec.append("\n")

        # ---- background ----
        if self.background:
            fig, ax = plt.subplots(figsize=(6, 4))
            filters = sorted(self.background.keys())
            bg_vals = [self.background[f] for f in filters]
            colors = {"J": "#4C72B0", "H": "#55A868", "Ks": "#C44E52"}
            bars = ax.bar(filters, bg_vals,
                          color=[colors.get(f, "#888") for f in filters])
            ax.set_ylabel("Sky background [e-/s/pixel]")
            ax.set_title(f"{INSTRUMENT} sky background (airmass=1.2)")
            ax.grid(True, alpha=0.3, axis="y")
            for bar, val in zip(bars, bg_vals):
                ax.text(bar.get_x() + bar.get_width() / 2, val + 20,
                        f"{val:.0f}", ha="center", va="bottom", fontsize=9)
            fig.tight_layout()
            fig.savefig(DOCS_DIR / "sky_background.png", dpi=150)
            plt.close(fig)

            sec.append("## Sky Background\n\n")
            sec.append("![Sky background](sky_background.png)\n\n")

        # ---- noise budget ----
        if self.lim_mag:
            sec.append("## Noise Budget at Limiting Magnitude\n\n")
            sec.append(
                "| Filter | Sky BG | Peak S/N |\n"
                "|--------|-------:|---------:|\n"
            )
            for filt in sorted(self.lim_mag):
                d = self.lim_mag[filt]
                sec.append(
                    f"| {filt:6s} | {d['bg_rate']:5.0f} e-/s/pix | "
                    f"{d['ref_signal']:7.0f} |\n"
                )
            sec.append("\n")

        if not self.lim_mag and not self.throughput:
            sec.append(
                "*No radiometry data. Run with `pytest -k slow`.*\n")

        (DOCS_DIR / "radiometry_report.md").write_text(
            "".join(sec), encoding="utf-8")


_report = _Report()


@pytest.fixture(scope="module")
def orig_report():
    return _report


@pytest.fixture(scope="session", autouse=True)
def _write_orig_report():
    """Write the report after all tests in this file complete."""
    yield
    _report.write()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_opt(**extra_props):
    """Build OpticalTrain for the original HAWKI with skycalc disabled."""
    props = {"!ATMO.skycalc_atmosphere.include": False}
    props.update(extra_props)
    return scopesim.OpticalTrain(
        scopesim.UserCommands(use_instrument=INSTRUMENT,
                              properties=props))


def _make_opt_with_atmo(**extra_props):
    """Build OpticalTrain with atmosphere.  Skips if skycalc unreachable."""
    props = {
        "!OBS.airmass": 1.2,
        "!SIM.spectral.spectral_resolution": 1000,
        "!SIM.spectral.spectral_bin_width": 0.001,
    }
    props.update(extra_props)
    cmd = scopesim.UserCommands(use_instrument=INSTRUMENT,
                                properties=props)
    try:
        return scopesim.OpticalTrain(cmd)
    except Exception as exc:
        pytest.skip(f"Skycalc server unreachable: {exc}")


def _aperture_snr(det, x, y, r0, r1, r2):
    """Aperture photometry on a readout frame."""
    sig_box = det[y - r0:y + r0 + 1, x - r0:x + r0 + 1]
    ann_box = det[y - r2:y + r2 + 1, x - r2:x + r2 + 1].copy()
    off = r2 - r1
    ann_box[off:-off, off:-off] = np.nan
    ann_pixels = ann_box[np.isfinite(ann_box)]
    if len(ann_pixels) < 10:
        return 0.0
    bg_median = float(np.median(ann_pixels))
    bg_std = float(np.std(ann_pixels))
    n_pix = sig_box.size
    signal = float(np.sum(sig_box)) - bg_median * n_pix
    noise = bg_std * np.sqrt(n_pix) * np.sqrt(2)
    return signal / noise if noise > 0 else 0.0


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestOrigPackageLoading:
    def test_user_commands_loads(self):
        cmd = scopesim.UserCommands(use_instrument=INSTRUMENT)
        assert isinstance(cmd, scopesim.UserCommands)
        for key in ["SIM", "OBS", "ATMO", "TEL", "INST", "DET"]:
            assert key in cmd and len(cmd[key]) > 0

    def test_pixel_scale(self):
        cmd = scopesim.UserCommands(use_instrument=INSTRUMENT)
        assert cmd["!INST.pixel_scale"] == approx(0.106, rel=1e-2)


class TestOrigOpticalTrain:
    def test_creates_successfully(self):
        opt = _make_opt()
        assert isinstance(opt, scopesim.OpticalTrain)

    def test_system_throughput_nonzero(self):
        opt = _make_opt()
        wave = np.linspace(0.8, 2.5, 171) * u.um
        tc = opt.optics_manager.system_transmission()
        assert np.max(tc(wave)).value > 0.2


class TestOrigFilterCoverage:
    @pytest.mark.parametrize("filter_name", [
        "Y", "J", "H", "Ks", "BrGamma", "CH4",
    ])
    def test_filter_loads(self, filter_name, orig_report):
        opt = _make_opt(**{"!OBS.filter_name": filter_name})
        wave = np.linspace(0.8, 2.5, 1701) * u.um
        tc = opt.optics_manager.system_transmission()
        tc_vals = tc(wave)
        orig_report.throughput[filter_name] = (
            wave.value, np.array(tc_vals.value, dtype=float))
        assert np.max(tc_vals).value > 0.01


# ---------------------------------------------------------------------------
# Radiometry (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestOrigStarFieldPhotometry:
    """Same star-field photometry test as HAWKI_new, against original HAWKI."""

    @pytest.mark.parametrize(
        ("filter_name", "eso_lim_mag", "tolerance"), [
            ("J", 23.9, 5.0),
            ("H", 22.5, 5.0),
            ("Ks", 22.3, 5.0),
        ],
    )
    def test_star_field_snr(self, filter_name, eso_lim_mag, tolerance,
                            orig_report):
        from scipy.stats import linregress

        n_stars = 225
        mmin, mmax = 15, 25
        r0 = 4
        r1 = 10
        r2 = 15

        src = st.star_field(n_stars, mmin, mmax, width=360, use_grid=True)
        star_mags = np.linspace(mmin, mmax, n_stars)

        opt = _make_opt_with_atmo(**{
            "!OBS.filter_name": filter_name,
            "!OBS.dit": 3600,
            "!OBS.ndit": 1,
        })
        # Original HAWKI defaults to a 1024-pixel window — switch to
        # the full 4-detector mosaic, matching HAWKI_new behaviour.
        opt["detector_1024_window"].include = False
        opt["detector_array_list"].include = True
        opt["detector_linearity"].include = False

        opt.observe(src)
        hdus = opt.readout()[0]

        ip_data = opt.image_planes[0].hdu.data
        ip_h = opt.image_planes[0].hdu.header
        bg_rate = float(np.median(ip_data))

        # Calibrate arcsec -> mm offset from brightest star
        plate_scale = opt.cmds["!INST.pixel_scale"] / ip_h["CDELT1D"]
        src_x = np.array(src.fields[0].field["x"], dtype=float)
        src_y = np.array(src.fields[0].field["y"], dtype=float)

        peak_y, peak_x = np.unravel_index(np.argmax(ip_data), ip_data.shape)
        peak_mm_x = ((peak_x - ip_h["CRPIX1D"]) * ip_h["CDELT1D"]
                      + ip_h["CRVAL1D"])
        peak_mm_y = ((peak_y - ip_h["CRPIX2D"]) * ip_h["CDELT2D"]
                      + ip_h["CRVAL2D"])

        offset_x = peak_mm_x - src_x[0] / plate_scale
        offset_y = peak_mm_y - src_y[0] / plate_scale

        mm_x = src_x / plate_scale + offset_x
        mm_y = src_y / plate_scale + offset_y

        # Aperture photometry on detector readouts
        measured_mags = []
        measured_snrs = []

        for det_idx in range(1, len(hdus)):
            det_data = hdus[det_idx].data.astype(float)
            dh = hdus[det_idx].header
            if "CRVAL1D" not in dh:
                continue

            dx = (mm_x - dh["CRVAL1D"]) / dh["CDELT1D"] + dh["CRPIX1D"]
            dy = (mm_y - dh["CRVAL2D"]) / dh["CDELT2D"] + dh["CRPIX2D"]

            margin = r2 + 5
            ny_det, nx_det = det_data.shape
            on_det = ((dx > margin) & (dx < nx_det - margin) &
                      (dy > margin) & (dy < ny_det - margin))

            for ix, iy, mag in zip(dx[on_det].astype(int),
                                   dy[on_det].astype(int),
                                   star_mags[on_det]):
                snr = _aperture_snr(det_data, ix, iy, r0, r1, r2)
                measured_mags.append(mag)
                measured_snrs.append(snr)

        measured_mags = np.array(measured_mags)
        measured_snrs = np.array(measured_snrs)

        print(f"{filter_name}: measured S/N for {len(measured_mags)} stars, "
              f"bg={bg_rate:.0f} e-/s/pix")

        # Fit S/N in [10, 400]
        fit_mask = (measured_snrs >= 10) & (measured_snrs <= 400)
        if np.sum(fit_mask) < 10:
            pytest.skip(
                f"Too few stars in fit range ({np.sum(fit_mask)})")

        fit = linregress(measured_mags[fit_mask],
                         np.log10(measured_snrs[fit_mask]))
        lim_mag = (np.log10(5) - fit.intercept) / fit.slope

        print(f"{filter_name}: ESO={eso_lim_mag:.1f}, "
              f"ScopeSim={lim_mag:.1f}, "
              f"delta={lim_mag - eso_lim_mag:+.1f}, "
              f"fit R^2={fit.rvalue**2:.3f}")

        readout_image = hdus[1].data.astype(float)

        orig_report.lim_mag[filter_name] = {
            "eso_lim_mag": eso_lim_mag,
            "scopesim_lim_mag": round(lim_mag, 1),
            "bg_rate": bg_rate,
            "ref_signal": float(np.max(measured_snrs)),
            "mags": measured_mags,
            "snrs": measured_snrs,
            "fit_slope": fit.slope,
            "fit_intercept": fit.intercept,
        }
        orig_report.star_field[filter_name] = {
            "image": readout_image,
            "bg_rate": bg_rate,
        }
        orig_report.background[filter_name] = bg_rate

        assert lim_mag == approx(eso_lim_mag, abs=tolerance), \
            (f"{filter_name}-band limiting mag {lim_mag:.1f} differs from "
             f"ESO {eso_lim_mag:.1f} by {abs(lim_mag - eso_lim_mag):.1f}")
