"""Tests for the MAVIS instrument package."""

from pathlib import Path

import numpy as np
import pytest
from astropy import units as u

import scopesim
from scopesim import rc

PATH_HERE = Path(__file__).parent
PATH_IRDB = PATH_HERE.parent.parent
rc.__config__["!SIM.file.local_packages_path"] = str(PATH_IRDB)

MAVIS_DIR = Path(__file__).parent.parent
FILTER_NAMES = ["B", "V", "R", "I", "u", "g", "r_SDSS", "i_SDSS", "z"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def mavis_cmd():
    return scopesim.UserCommands(
        use_instrument="MAVIS",
        properties={"!ATMO.skycalc_atmosphere.include": False},
    )


@pytest.fixture(scope="module")
def mavis_opt(mavis_cmd):
    return scopesim.OpticalTrain(mavis_cmd)


# ---------------------------------------------------------------------------
# Package loading
# ---------------------------------------------------------------------------

class TestPackageLoading:
    def test_user_commands_loads(self):
        cmd = scopesim.UserCommands(use_instrument="MAVIS")
        assert cmd is not None

    def test_optical_train_builds(self, mavis_opt):
        assert mavis_opt is not None

    def test_default_filter_is_V(self, mavis_cmd):
        assert mavis_cmd["!OBS.filter_name"] == "V"

    def test_pixel_scale(self, mavis_cmd):
        assert mavis_cmd["!INST.pixel_scale"] == pytest.approx(0.00736, rel=1e-3)

    def test_detector_mode_slow(self, mavis_cmd):
        assert mavis_cmd["!OBS.detector_readout_mode"] == "slow"


# ---------------------------------------------------------------------------
# Detector geometry
# ---------------------------------------------------------------------------

class TestDetector:
    def test_readout_has_two_dims(self, mavis_opt):
        from scopesim.source import source_templates as st
        src = st.empty_sky()
        mavis_opt.observe(src, update=True)
        hdus = mavis_opt.readout()
        img = hdus[0][1].data
        assert img.ndim == 2

    def test_readout_shape(self, mavis_opt):
        """Detector should be 4004 rows x 4096 columns."""
        from scopesim.source import source_templates as st
        src = st.empty_sky()
        mavis_opt.observe(src, update=True)
        hdus = mavis_opt.readout()
        img = hdus[0][1].data
        assert img.shape == (4004, 4096)


# ---------------------------------------------------------------------------
# Filter wheel
# ---------------------------------------------------------------------------

class TestFilterWheel:
    @pytest.mark.parametrize("filter_name", FILTER_NAMES)
    def test_filter_file_exists(self, filter_name):
        fpath = MAVIS_DIR / "filters" / f"TC_filter_{filter_name}.dat"
        assert fpath.exists(), f"Filter file missing: {fpath}"

    @pytest.mark.parametrize("filter_name", FILTER_NAMES)
    def test_filter_has_nonzero_throughput(self, filter_name, report):
        cmd = scopesim.UserCommands(
            use_instrument="MAVIS",
            properties={
                "!OBS.filter_name": filter_name,
                "!ATMO.skycalc_atmosphere.include": False,
            },
        )
        opt = scopesim.OpticalTrain(cmd)
        wave = np.linspace(0.32, 1.00, 1000) * u.um
        tc = opt.optics_manager.system_transmission(plot=False)
        tc_vals = tc(wave)
        max_tc = float(np.max(tc_vals.value))
        assert max_tc > 0.01, (
            f"Filter {filter_name}: max throughput {max_tc:.4f} is too low"
        )
        report.throughput[filter_name] = (
            wave.value, np.array(tc_vals.value, dtype=float)
        )


# ---------------------------------------------------------------------------
# Basic photometry (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestPhotometry:
    def test_point_source_above_sky(self, mavis_opt):
        """A bright star should produce signal well above sky background."""
        from scopesim.source import source_templates as st
        src = st.star(filter_name="V", magnitude=15)
        mavis_opt.observe(src, update=True)
        hdus = mavis_opt.readout()
        img = hdus[0][1].data.astype(float)
        cx, cy = img.shape[1] // 2, img.shape[0] // 2
        signal_box = img[cy - 5:cy + 5, cx - 5:cx + 5]
        sky_annulus = img[cy - 30:cy + 30, cx - 30:cx + 30]
        sky_med = np.median(sky_annulus)
        assert np.max(signal_box) > sky_med * 2
