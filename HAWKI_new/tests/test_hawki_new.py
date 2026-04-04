"""
Tests for the HAWKI_new instrument package.

Unit tests verify package loading, OpticalTrain construction, detector geometry,
and system throughput. Radiometry tests validate limiting magnitudes against
ESO reference values.

ESO limiting magnitudes (S/N=5, point source, 3600s, 0.8" seeing, airmass 1.2):
    J:  23.9 Vega mag
    H:  22.5 Vega mag
    Ks: 22.3 Vega mag
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def hawki_cmd():
    """UserCommands for HAWKI_new with skycalc disabled."""
    return scopesim.UserCommands(
        use_instrument="HAWKI_new",
        properties={"!ATMO.skycalc_atmosphere.include": False},
    )


@pytest.fixture(scope="module")
def hawki_opt(hawki_cmd):
    """OpticalTrain built from HAWKI_new (no atmosphere)."""
    return scopesim.OpticalTrain(hawki_cmd)


@pytest.fixture(scope="module")
def hawki_readout(hawki_opt):
    """Single readout of an empty sky (no atmosphere)."""
    src = st.empty_sky()
    hawki_opt.observe(src)
    return hawki_opt.readout()


def _make_opt_with_atmo(**extra_props):
    """Build an OpticalTrain with the skycalc atmosphere enabled.

    Uses coarse spectral resolution (R=1000) to speed up the skycalc query.
    Raises pytest.skip if the ESO skycalc server is unreachable.
    """
    props = {
        "!OBS.airmass": 1.2,
        "!OBS.seeing": 0.8,
        "!SIM.spectral.spectral_resolution": 1000,
        "!SIM.spectral.spectral_bin_width": 0.001,
    }
    props.update(extra_props)
    cmd = scopesim.UserCommands(use_instrument="HAWKI_new",
                                properties=props)
    try:
        opt = scopesim.OpticalTrain(cmd)
    except Exception as exc:
        pytest.skip(f"Skycalc server unreachable: {exc}")
    return opt


# ---------------------------------------------------------------------------
# Unit tests - package loading
# ---------------------------------------------------------------------------

class TestPackageLoading:
    def test_user_commands_loads(self):
        cmd = scopesim.UserCommands(use_instrument="HAWKI_new")
        assert isinstance(cmd, scopesim.UserCommands)
        for key in ["SIM", "OBS", "ATMO", "TEL", "INST", "DET"]:
            assert key in cmd and len(cmd[key]) > 0

    def test_default_filter_is_ks(self, hawki_cmd):
        assert hawki_cmd["!OBS.filter_name"] == "Ks"

    def test_pixel_scale(self, hawki_cmd):
        assert hawki_cmd["!INST.pixel_scale"] == approx(0.1064, rel=1e-3)


class TestOpticalTrain:
    def test_creates_successfully(self, hawki_opt):
        assert isinstance(hawki_opt, scopesim.OpticalTrain)

    def test_has_required_effects(self, hawki_opt):
        effect_names = set()
        for oe in hawki_opt.optics_manager.optical_elements:
            for eff in oe.effects:
                effect_names.add(eff.meta.get("name"))

        required = [
            "vlt_mirror_list",
            "vlt_generic_psf",
            "hawki_field_of_view",
            "hawki_mirror_list",
            "filter_wheel",
            "detector_array_list",
            "qe_curve",
            "exposure_action",
            "dark_current",
            "shot_noise",
            "detector_linearity",
            "readout_noise",
            "hawki_seeing_psf",
        ]
        for name in required:
            assert name in effect_names, f"Missing effect: {name}"

    def test_system_throughput_nonzero(self, hawki_opt):
        wave = np.linspace(0.8, 2.5, 171) * u.um
        tc = hawki_opt.optics_manager.system_transmission()
        throughput = tc(wave)
        assert np.max(throughput).value > 0.3, "Peak system throughput too low"
        assert np.max(throughput).value < 0.8, "Peak system throughput too high"

    def test_fov_count(self, hawki_opt):
        assert len(hawki_opt.fov_manager.fovs) == 9


# ---------------------------------------------------------------------------
# Unit tests - detector geometry and readout
# ---------------------------------------------------------------------------

class TestDetectorReadout:
    def test_four_detectors_2048x2048(self, hawki_readout):
        hdul = hawki_readout[0]
        assert len(hdul) == 5, "Expected 1 primary + 4 detector extensions"
        for i in range(1, 5):
            assert hdul[i].data.shape == (2048, 2048), \
                f"Detector {i} shape mismatch"

    def test_output_is_float32(self, hawki_readout):
        hdul = hawki_readout[0]
        for i in range(1, 5):
            assert hdul[i].data.dtype == np.float32

    def test_reference_border_has_less_signal(self, hawki_readout):
        """The 4-pixel reference border should have much less signal than
        the interior. Readout noise still fills the border, but the
        science signal is zeroed by ReferencePixelBorder."""
        hdul = hawki_readout[0]
        for i in range(1, 5):
            data = hdul[i].data
            border = np.concatenate([
                data[:4, 4:-4].ravel(),
                data[-4:, 4:-4].ravel(),
                data[4:-4, :4].ravel(),
                data[4:-4, -4:].ravel(),
            ])
            inner = data[10:-10, 10:-10].ravel()

            # Border median should be much lower than interior median
            assert np.abs(np.median(border)) < np.median(inner) * 0.01, \
                f"Det {i}: border signal not suppressed relative to interior"

    def test_readout_scales_with_dit(self):
        """Check that the detector output scales roughly linearly with DIT.
        This validates the exposure integration chain."""
        results = {}
        for dit in [10, 60]:
            cmd = scopesim.UserCommands(
                use_instrument="HAWKI_new",
                properties={
                    "!ATMO.skycalc_atmosphere.include": False,
                    "!OBS.dit": dit,
                    "!OBS.ndit": 1,
                },
            )
            opt = scopesim.OpticalTrain(cmd)
            opt["shot_noise"].include = False
            opt["readout_noise"].include = False
            opt["detector_linearity"].include = False

            src = st.empty_sky()
            opt.observe(src)
            hdul = opt.readout()[0]
            results[dit] = np.median(hdul[1].data[10:-10, 10:-10])

        ratio = results[60] / results[10]
        assert ratio == approx(6.0, rel=0.1), \
            f"DIT scaling ratio {ratio:.2f}, expected ~6.0"


# ---------------------------------------------------------------------------
# Radiometry tests - limiting magnitudes
# ---------------------------------------------------------------------------

class TestFilterCoverage:
    """Test that all 11 filters load and produce nonzero throughput."""

    @pytest.mark.parametrize("filter_name", [
        "Y", "J", "H", "Ks",
        "BrGamma", "CH4", "H2",
        "NB0984", "NB1060", "NB1190", "NB2090",
    ])
    def test_filter_loads(self, filter_name, report):
        cmd = scopesim.UserCommands(
            use_instrument="HAWKI_new",
            properties={
                "!OBS.filter_name": filter_name,
                "!ATMO.skycalc_atmosphere.include": False,
            },
        )
        opt = scopesim.OpticalTrain(cmd)
        wave = np.linspace(0.8, 2.5, 1701) * u.um
        tc = opt.optics_manager.system_transmission()
        tc_vals = tc(wave)

        # Record for report
        report.throughput[filter_name] = (
            wave.value, np.array(tc_vals.value, dtype=float)
        )

        assert np.max(tc_vals).value > 0.01, \
            f"Filter {filter_name} gives zero throughput"


@pytest.mark.slow
class TestStarFieldPhotometry:
    """
    Observe a 15x15 star field covering the full HAWKI focal plane and
    measure per-star S/N from the *readout* frames using proper aperture
    photometry (signal in inner box, noise from std in annulus).

    The star field spans 360 arcsec and magnitudes 15-25.  Stars are
    detected in the noise-free image plane, mapped to detector pixel
    coordinates via the focal-plane mm WCS, and measured on the noisy
    readout frames.

    Also validates the limiting magnitude against the ESO reference.

    Reference (ESO HAWK-I Overview):
        S/N=5, point source, 3600s on-source, 0.8" seeing, airmass 1.2
        J:  23.9 Vega mag
        H:  22.5 Vega mag
        Ks: 22.3 Vega mag
    """

    @pytest.mark.parametrize(
        ("filter_name", "eso_lim_mag", "tolerance"), [
            ("J", 23.9, 1.5),
            ("H", 22.5, 1.5),
            ("Ks", 22.3, 1.5),
        ],
    )
    def test_star_field_snr(self, filter_name, eso_lim_mag, tolerance,
                            report):
        from scipy.stats import linregress

        n_stars = 225          # 15x15 grid
        mmin, mmax = 15, 25    # full observable range
        r0 = 4                 # signal half-box  (9x9 aperture)
        r1 = 10                # inner annulus radius
        r2 = 15                # outer annulus radius

        src = st.star_field(n_stars, mmin, mmax, width=360, use_grid=True)
        star_mags = np.linspace(mmin, mmax, n_stars)

        opt = _make_opt_with_atmo(**{
            "!OBS.filter_name": filter_name,
            "!OBS.dit": 3600,
            "!OBS.ndit": 1,
        })
        opt["detector_linearity"].include = False

        # ---- observe + readout ----
        opt.observe(src)
        hdus = opt.readout()[0]   # noisy detector frames

        ip_data = opt.image_planes[0].hdu.data
        ip_h = opt.image_planes[0].hdu.header
        bg_rate = float(np.median(ip_data))

        # ---- map known star positions to focal-plane mm ----
        # Simple arcsec/plate_scale has a systematic offset, so calibrate
        # using the brightest star (easily found via argmax on image plane).
        plate_scale = opt.cmds["!INST.plate_scale"]   # arcsec / mm
        src_x = np.array(src.fields[0].field["x"], dtype=float)
        src_y = np.array(src.fields[0].field["y"], dtype=float)

        # Brightest star (lowest mag) in the image plane
        peak_y, peak_x = np.unravel_index(np.argmax(ip_data), ip_data.shape)
        peak_mm_x = ((peak_x - ip_h["CRPIX1D"]) * ip_h["CDELT1D"]
                      + ip_h["CRVAL1D"])
        peak_mm_y = ((peak_y - ip_h["CRPIX2D"]) * ip_h["CDELT2D"]
                      + ip_h["CRVAL2D"])

        bright_idx = 0   # star_field creates brightest first
        offset_x = peak_mm_x - src_x[bright_idx] / plate_scale
        offset_y = peak_mm_y - src_y[bright_idx] / plate_scale

        mm_x = src_x / plate_scale + offset_x
        mm_y = src_y / plate_scale + offset_y

        # ---- aperture photometry on each detector readout ----
        measured_mags = []
        measured_snrs = []

        for det_idx in range(1, 5):
            det_data = hdus[det_idx].data.astype(float)
            dh = hdus[det_idx].header

            # focal-plane mm -> detector pixel via the "D" WCS
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

        print(f"{filter_name}: measured S/N for {len(measured_mags)} stars "
              f"across 4 detectors, bg={bg_rate:.0f} e-/s/pix")

        # ---- fit log(S/N) vs mag and find limiting magnitude ----
        # Restrict fit to S/N in [10, 400]: avoids saturation at the
        # bright end and noise-dominated scatter at the faint end.
        fit_mask = (measured_snrs >= 10) & (measured_snrs <= 400)
        if np.sum(fit_mask) < 10:
            pytest.skip(
                f"Too few stars with 10<S/N<400 ({np.sum(fit_mask)})")

        fit = linregress(measured_mags[fit_mask],
                         np.log10(measured_snrs[fit_mask]))
        snr_limit = 5
        lim_mag = (np.log10(snr_limit) - fit.intercept) / fit.slope

        print(f"{filter_name}: ESO={eso_lim_mag:.1f}, "
              f"ScopeSim={lim_mag:.1f}, "
              f"delta={lim_mag - eso_lim_mag:+.1f}, "
              f"fit R^2={fit.rvalue**2:.3f}")

        # ---- save a detector readout for the report ----
        readout_image = hdus[1].data.astype(float)

        # ---- record results for report ----
        report.lim_mag[filter_name] = {
            "eso_lim_mag": eso_lim_mag,
            "scopesim_lim_mag": round(lim_mag, 1),
            "bg_rate": bg_rate,
            "ref_signal": float(np.max(measured_snrs)),
            "mags": measured_mags,
            "snrs": measured_snrs,
            "fit_slope": fit.slope,
            "fit_intercept": fit.intercept,
        }
        report.star_field[filter_name] = {
            "image": readout_image,
            "bg_rate": bg_rate,
        }
        report.background[filter_name] = bg_rate

        assert lim_mag == approx(eso_lim_mag, abs=tolerance), \
            (f"{filter_name}-band limiting mag {lim_mag:.1f} differs from "
             f"ESO {eso_lim_mag:.1f} by {abs(lim_mag - eso_lim_mag):.1f} "
             f"mag (tolerance {tolerance})")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _aperture_snr(det, x, y, r0, r1, r2):
    """Aperture photometry with annulus noise estimate on a readout frame.

    Parameters
    ----------
    det : 2-D array  – detector readout [ADU or e-]
    x, y : int        – centre pixel
    r0 : int          – signal half-box radius
    r1, r2 : int      – inner/outer annulus radii
    """
    sig_box = det[y - r0:y + r0 + 1, x - r0:x + r0 + 1]
    ann_box = det[y - r2:y + r2 + 1, x - r2:x + r2 + 1].copy()
    # mask out the inner region to leave only the annulus
    off = r2 - r1
    ann_box[off:-off, off:-off] = np.nan
    ann_pixels = ann_box[np.isfinite(ann_box)]

    if len(ann_pixels) < 10:
        return 0.0

    bg_median = float(np.median(ann_pixels))
    bg_std = float(np.std(ann_pixels))
    n_pix = sig_box.size
    signal = float(np.sum(sig_box)) - bg_median * n_pix
    # sqrt(2) accounts for noise in the background estimate itself
    noise = bg_std * np.sqrt(n_pix) * np.sqrt(2)

    return signal / noise if noise > 0 else 0.0
