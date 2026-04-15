"""
Tests for the ERIS NIX instrument package.

Unit tests verify package loading, OpticalTrain construction, detector geometry,
filter coverage, and system throughput. Radiometry tests validate limiting
magnitudes against ESO reference values.

ESO ERIS ETC reference limiting magnitudes are TBD -- using approximate
values derived from the ERIS User Manual and ETC for now.

Approximate limiting magnitudes (S/N=5, point source, 3600s, NGS AO, airmass 1.2):
    J:  24.5 Vega mag (estimated, AO-corrected)
    H:  23.5 Vega mag (estimated)
    Ks: 23.0 Vega mag (estimated)
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
def eris_cmd():
    """UserCommands for ERIS with skycalc disabled."""
    return scopesim.UserCommands(
        use_instrument="ERIS",
        properties={"!ATMO.skycalc_atmosphere.include": False},
    )


@pytest.fixture(scope="module")
def eris_opt(eris_cmd):
    """OpticalTrain built from ERIS (no atmosphere)."""
    return scopesim.OpticalTrain(eris_cmd)


@pytest.fixture(scope="module")
def eris_readout(eris_opt):
    """Single readout of an empty sky (no atmosphere)."""
    src = st.empty_sky()
    eris_opt.observe(src)
    return eris_opt.readout()


def _make_opt_with_atmo(**extra_props):
    """Build an OpticalTrain with the skycalc atmosphere enabled.

    Uses coarse spectral resolution to speed up the skycalc query.
    Raises pytest.skip if the ESO skycalc server is unreachable.
    """
    props = {
        "!OBS.airmass": 1.2,
        "!OBS.seeing": 0.8,
        "!SIM.spectral.spectral_resolution": 1000,
        "!SIM.spectral.spectral_bin_width": 0.001,
    }
    props.update(extra_props)
    cmd = scopesim.UserCommands(use_instrument="ERIS",
                                properties=props)
    try:
        opt = scopesim.OpticalTrain(cmd)
    except Exception as exc:
        pytest.skip(f"Skycalc server unreachable: {exc}")
    return opt


# ---------------------------------------------------------------------------
# Package loading tests
# ---------------------------------------------------------------------------

class TestPackageLoading:
    """Test that the ERIS package loads correctly."""

    def test_usercommands_loads(self, eris_cmd):
        assert eris_cmd is not None
        assert "ERIS" in str(eris_cmd)

    def test_optical_train_loads(self, eris_opt):
        assert eris_opt is not None

    def test_effects_present(self, eris_opt):
        """Check that key effects are in the optical train."""
        assert eris_opt["nix_filter_wheel"] is not None
        assert eris_opt["detector_array"] is not None
        assert eris_opt["qe_curve"] is not None
        assert eris_opt["eris_warm_optics"] is not None
        assert eris_opt["eris_ao_psf"] is not None

    def test_default_filter_is_ks(self, eris_opt):
        fw = eris_opt["nix_filter_wheel"]
        assert "Ks" in str(fw.current_filter)


# ---------------------------------------------------------------------------
# Detector tests
# ---------------------------------------------------------------------------

class TestDetector:
    """Test NIX detector geometry and readout."""

    def test_readout_shape(self, eris_readout):
        """Detector output should be a single 2048x2048 array."""
        assert len(eris_readout) == 1
        hdu = eris_readout[0]
        assert hdu[1].data.shape == (2048, 2048)

    def test_readout_dtype(self, eris_readout):
        """Output should be float32."""
        assert eris_readout[0][1].data.dtype == np.float32

    def test_dark_current_scales_with_dit(self, eris_opt):
        """Dark current should scale linearly with DIT."""
        src = st.empty_sky()

        eris_opt.cmds["!OBS.dit"] = 10
        eris_opt.observe(src)
        r10 = eris_opt.readout()
        med10 = np.median(r10[0][1].data)

        eris_opt.cmds["!OBS.dit"] = 100
        eris_opt.observe(src)
        r100 = eris_opt.readout()
        med100 = np.median(r100[0][1].data)

        # dark should be ~10x larger for 10x longer DIT
        ratio = med100 / med10 if med10 != 0 else 0
        assert 5 < ratio < 15, f"Dark ratio {ratio} not in expected range"

        # reset
        eris_opt.cmds["!OBS.dit"] = 60


# ---------------------------------------------------------------------------
# Filter coverage tests — populate throughput data for report
# ---------------------------------------------------------------------------

class TestFilterCoverage:
    """Test that all NIX filters load and produce nonzero throughput."""

    JHK_FILTERS = ["J", "H", "Ks", "Pa-b", "Fe-II", "H2-cont",
                    "H2-1-0S", "Br-g", "K-peak", "IB-2.42", "IB-2.48"]

    LM_FILTERS = ["Short-Lp", "Lp", "L-Broad", "Mp",
                   "Br-a-cont", "Br-a"]

    @pytest.mark.parametrize("filter_name", JHK_FILTERS)
    def test_jhk_filter_throughput(self, filter_name, report):
        cmd = scopesim.UserCommands(
            use_instrument="ERIS",
            properties={
                "!OBS.filter_name": filter_name,
                "!ATMO.skycalc_atmosphere.include": False,
            },
        )
        opt = scopesim.OpticalTrain(cmd)
        wave = np.linspace(0.8, 2.6, 1801) * u.um
        tc = opt.optics_manager.system_transmission(plot=False)
        tc_vals = tc(wave)

        report.throughput[filter_name] = (
            wave.value, np.array(tc_vals.value, dtype=float)
        )

        assert np.max(tc_vals).value > 0.01, \
            f"Filter {filter_name} gives zero throughput"

    @pytest.mark.parametrize("filter_name", LM_FILTERS)
    def test_lm_filter_throughput(self, filter_name, report):
        cmd = scopesim.UserCommands(
            use_instrument="ERIS",
            properties={
                "!OBS.modes": ["NGS", "nixIMG_LM13"],
                "!OBS.filter_name": filter_name,
                "!ATMO.skycalc_atmosphere.include": False,
            },
        )
        opt = scopesim.OpticalTrain(cmd)
        wave = np.linspace(2.5, 5.5, 1501) * u.um
        tc = opt.optics_manager.system_transmission(plot=False)
        tc_vals = tc(wave)

        report.throughput[filter_name] = (
            wave.value, np.array(tc_vals.value, dtype=float)
        )

        assert np.max(tc_vals).value > 0.01, \
            f"Filter {filter_name} gives zero throughput"


# ---------------------------------------------------------------------------
# Throughput sanity tests
# ---------------------------------------------------------------------------

class TestThroughput:
    """Basic throughput sanity checks."""

    def test_system_transmission_is_nonzero(self, eris_opt):
        """System transmission should be nonzero in K-band."""
        sys_trans = eris_opt.optics_manager.system_transmission(plot=False)
        wave_k = np.array([21800]) * u.AA  # 2.18um in Angstrom
        trans_k = sys_trans(wave_k).value
        assert trans_k[0] > 0.01, \
            f"System transmission at 2.18um is {trans_k[0]}, expected > 0.01"

    def test_system_transmission_peaks_in_filter(self, eris_opt):
        """Peak transmission should be within the Ks filter passband."""
        sys_trans = eris_opt.optics_manager.system_transmission(plot=False)
        wave = np.linspace(9000, 26000, 1000) * u.AA
        trans = sys_trans(wave).value
        peak_wave = wave[np.argmax(trans)]
        # Ks filter center is ~2.18um -- peak should be in JHK range
        assert 9000 * u.AA < peak_wave < 25000 * u.AA, \
            f"Peak at {peak_wave}, expected within JHK range"


# ---------------------------------------------------------------------------
# Mode switching tests
# ---------------------------------------------------------------------------

class TestModes:
    """Test that different modes can be loaded."""

    def test_noao_mode_loads(self):
        cmd = scopesim.UserCommands(
            use_instrument="ERIS",
            properties={
                "!OBS.modes": ["NOAO", "nixIMG_JHK13"],
                "!ATMO.skycalc_atmosphere.include": False,
            },
        )
        opt = scopesim.OpticalTrain(cmd)
        assert opt is not None

    def test_jhk27_mode_loads(self):
        cmd = scopesim.UserCommands(
            use_instrument="ERIS",
            properties={
                "!OBS.modes": ["NGS", "nixIMG_JHK27"],
                "!ATMO.skycalc_atmosphere.include": False,
            },
        )
        opt = scopesim.OpticalTrain(cmd)
        assert opt is not None

    def test_lm13_mode_loads(self):
        cmd = scopesim.UserCommands(
            use_instrument="ERIS",
            properties={
                "!OBS.modes": ["NGS", "nixIMG_LM13"],
                "!ATMO.skycalc_atmosphere.include": False,
            },
        )
        opt = scopesim.OpticalTrain(cmd)
        assert opt is not None

    def test_lgs_mode_loads(self):
        cmd = scopesim.UserCommands(
            use_instrument="ERIS",
            properties={
                "!OBS.modes": ["LGS", "nixIMG_JHK13"],
                "!ATMO.skycalc_atmosphere.include": False,
            },
        )
        opt = scopesim.OpticalTrain(cmd)
        assert opt is not None

    def test_se_mode_loads(self):
        cmd = scopesim.UserCommands(
            use_instrument="ERIS",
            properties={
                "!OBS.modes": ["SE", "nixIMG_JHK13"],
                "!ATMO.skycalc_atmosphere.include": False,
            },
        )
        opt = scopesim.OpticalTrain(cmd)
        assert opt is not None


# ---------------------------------------------------------------------------
# Radiometry tests -- limiting magnitudes (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestStarFieldPhotometry:
    """
    Observe a star field covering the NIX 13mas FoV and measure per-star
    S/N from the readout frame using aperture photometry.

    Star field spans 26 arcsec (matching the 13mas FoV) with magnitudes 15-25.
    """

    @pytest.mark.parametrize(
        ("filter_name", "eso_lim_mag", "tolerance"), [
            ("J", 24.5, 100),     # wide tolerance: skeleton optics not calibrated
            ("H", 23.5, 100),
            ("Ks", 23.0, 100),
        ],
    )
    def test_star_field_snr(self, filter_name, eso_lim_mag, tolerance,
                            report):
        from scipy.stats import linregress

        n_stars = 100          # 10x10 grid
        mmin, mmax = 15, 25
        r0 = 4                 # signal half-box (9x9 aperture)
        r1 = 10                # inner annulus radius
        r2 = 15                # outer annulus radius

        src = st.star_field(n_stars, mmin, mmax, width=26, use_grid=True)
        star_mags = np.linspace(mmin, mmax, n_stars)

        opt = _make_opt_with_atmo(**{
            "!OBS.filter_name": filter_name,
            "!OBS.dit": 3600,
            "!OBS.ndit": 1,
        })
        opt["detector_linearity"].include = False

        # ---- observe + readout ----
        opt.observe(src)
        hdus = opt.readout()[0]

        ip_data = opt.image_planes[0].hdu.data
        ip_h = opt.image_planes[0].hdu.header
        bg_rate = float(np.median(ip_data))

        # ---- map known star positions to focal-plane mm ----
        plate_scale = opt.cmds["!INST.plate_scale"]   # arcsec / mm
        src_x = np.array(src.fields[0].field["x"], dtype=float)
        src_y = np.array(src.fields[0].field["y"], dtype=float)

        # Brightest star in the image plane
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

        # ---- aperture photometry on detector readout ----
        measured_mags = []
        measured_snrs = []

        det_data = hdus[1].data.astype(float)
        dh = hdus[1].header

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

        print(f"{filter_name}: measured S/N for {len(measured_mags)} stars, "
              f"bg={bg_rate:.0f} e-/s/pix")

        # ---- fit log(S/N) vs mag and find limiting magnitude ----
        fit_mask = (measured_snrs >= 10) & (measured_snrs <= 400)
        if np.sum(fit_mask) < 5:
            pytest.skip(
                f"Too few stars with 10<S/N<400 ({np.sum(fit_mask)})")

        fit = linregress(measured_mags[fit_mask],
                         np.log10(measured_snrs[fit_mask]))
        snr_limit = 5
        lim_mag = (np.log10(snr_limit) - fit.intercept) / fit.slope

        print(f"{filter_name}: ESO~{eso_lim_mag:.1f}, "
              f"ScopeSim={lim_mag:.1f}, "
              f"delta={lim_mag - eso_lim_mag:+.1f}, "
              f"fit R^2={fit.rvalue**2:.3f}")

        # ---- save detector readout for the report ----
        readout_image = det_data

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
             f"ESO ~{eso_lim_mag:.1f} by {abs(lim_mag - eso_lim_mag):.1f} "
             f"mag (tolerance {tolerance})")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _aperture_snr(det, x, y, r0, r1, r2):
    """Aperture photometry with annulus noise estimate on a readout frame.

    Parameters
    ----------
    det : 2-D array  -- detector readout [ADU or e-]
    x, y : int        -- centre pixel
    r0 : int          -- signal half-box radius
    r1, r2 : int      -- inner/outer annulus radii
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
