"""Tests for the MAVIS instrument package."""

from pathlib import Path

import numpy as np

# numpy 2.0 renamed trapz to trapezoid; support both
trapezoid = getattr(np, "trapezoid", np.trapz)
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
            properties={"!OBS.filter_name": filter_name},
        )
        opt = scopesim.OpticalTrain(cmd)
        # Setting "!ATMO.skycalc_atmosphere.include" in the UserCommands
        # properties does *not* switch the effect off -- it has to be done on
        # the built train. Without this the reported curve carries telluric
        # absorption and the plot below is mislabelled.
        atmo = opt["skycalc_atmosphere"]
        atmo = atmo[0] if isinstance(atmo, list) else atmo
        atmo.include = False
        opt.update()

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
        from scopesim_templates.stellar import star
        src = star(filter_name="V", amplitude=15 * u.mag, spec_type="A0V")
        mavis_opt.observe(src, update=True)
        hdus = mavis_opt.readout()
        img = hdus[0][1].data.astype(float)
        cx, cy = img.shape[1] // 2, img.shape[0] // 2
        signal_box = img[cy - 5:cy + 5, cx - 5:cx + 5]
        sky_annulus = img[cy - 30:cy + 30, cx - 30:cx + 30]
        sky_med = np.median(sky_annulus)
        assert np.max(signal_box) > sky_med * 2


# ---------------------------------------------------------------------------
# PSF
# ---------------------------------------------------------------------------

class TestPSF:
    """The MCAO PSF must match MAVISIM at 550 nm and meet the ESO spec.

    The 550 nm plane is the on-axis end-to-end MCAO PSF from MAVISIM
    (LQG tomography simulations), measured at:
      Strehl at 550 nm            = 0.35
      Ensquared energy in 50 mas  = 0.40
    Both comfortably exceed the published floors (>8 % and >15 %,
    from background_info/mavis_baseline_specification.md).
    """

    @pytest.fixture(scope="class")
    def psf_hdus(self):
        from astropy.io import fits
        with fits.open(MAVIS_DIR / "PSF_MAVIS_mcao.fits") as hdul:
            yield [(h.header["WAVE0"], h.header, h.data.copy())
                   for h in hdul[1:]]

    def test_psf_file_exists(self):
        assert (MAVIS_DIR / "PSF_MAVIS_mcao.fits").exists()

    def test_550nm_plane_matches_mavisim(self, psf_hdus):
        """V-band photometry must track MAVISIM: same EE(50 mas)."""
        hdr = {w: h for w, h, _ in psf_hdus}[0.55]
        assert hdr["STREHL"] == pytest.approx(0.348, abs=0.01)
        assert hdr["EE50MAS"] == pytest.approx(0.399, abs=0.01)

    def test_every_plane_carries_unit_energy(self, psf_hdus):
        for wave, _, data in psf_hdus:
            assert float(data.sum()) == pytest.approx(1.0, rel=1e-4), \
                f"PSF plane at {wave} um does not sum to 1"

    def test_sampling_oversamples_the_detector(self, psf_hdus):
        """PSF pixels must be finer than the 7.36 mas detector pixels."""
        for wave, header, _ in psf_hdus:
            assert header["CUNIT1"] == "arcsec"
            assert header["CDELT1"] < 0.00736

    def test_strehl_meets_spec_at_550nm(self, psf_hdus):
        strehl = {w: h["STREHL"] for w, h, _ in psf_hdus}[0.55]
        assert strehl >= 0.08, f"Strehl {strehl:.3f} is below the >8% spec"

    def test_ensquared_energy_meets_spec_at_550nm(self, psf_hdus):
        ee50 = {w: h["EE50MAS"] for w, h, _ in psf_hdus}[0.55]
        assert ee50 >= 0.15, f"EE(50 mas) {ee50:.3f} is below the >15% spec"

    def test_strehl_increases_with_wavelength(self, psf_hdus):
        """Marechal: a fixed wavefront error corrects better in the red."""
        strehls = [h["STREHL"] for _, h, _ in sorted(psf_hdus, key=lambda x: x[0])]
        assert all(b > a for a, b in zip(strehls, strehls[1:])), strehls

    def test_core_is_at_the_array_centre(self, psf_hdus):
        for wave, _, data in psf_hdus:
            peak = np.unravel_index(np.argmax(data), data.shape)
            centre = (data.shape[0] // 2, data.shape[1] // 2)
            assert peak == centre, f"{wave} um: peak at {peak}, expected {centre}"

    def test_vlt_generic_psf_is_disabled(self, mavis_opt):
        """The MAVIS PSF is a delivered PSF; the VLT poppy PSF must not also
        be convolved in, or the AO core is broadened a second time."""
        rows = {r["name"]: r["included"] for r in mavis_opt.effects}
        assert not rows["vlt_generic_psf"]
        assert rows["mavis_ao_psf"]

    def test_tiptop_psf_is_available_but_disabled(self, mavis_opt):
        """The TipTop alternative must be present, off by default, and must
        never contact the TipTop server just by building the train."""
        rows = {r["name"]: r["included"] for r in mavis_opt.effects}
        assert not rows["mavis_tiptop_psf"]
        from scopesim.effects import TipTopPSF
        assert isinstance(mavis_opt["mavis_tiptop_psf"], TipTopPSF)


# ---------------------------------------------------------------------------
# Filter curves
# ---------------------------------------------------------------------------

# Literature effective wavelengths [um] of the standard passbands these
# filters implement. Compared against filter x CCD QE, not the filter alone:
# the SDSS z' *filter* is open-ended to the red (it runs out to 1.35 um) and
# it is the detector that closes the band, so a filter-only lambda_eff for z
# is meaningless.
FILTER_LAM_EFF = {
    "u": 0.356, "B": 0.426, "g": 0.470, "V": 0.545,
    "r_SDSS": 0.618, "R": 0.641, "i_SDSS": 0.749, "I": 0.798,
    "z": 0.895,
}
LAM_EFF_TOL = 0.03  # [um]


class TestFilterCurves:
    """The filters are real measured profiles, not top-hats."""

    @staticmethod
    def _read(name):
        from astropy.io import ascii as ioascii
        return ioascii.read(MAVIS_DIR / "filters" / f"TC_filter_{name}.dat")

    @pytest.mark.parametrize("name", FILTER_NAMES)
    def test_peak_transmission_is_realistic(self, name):
        """Real glass peaks well above 0.5 but never reaches 1.0."""
        tbl = self._read(name)
        peak = float(np.max(tbl["transmission"]))
        assert 0.5 < peak < 1.0, f"{name}: peak transmission {peak:.3f}"

    @pytest.mark.parametrize("name", FILTER_NAMES)
    def test_curve_is_finely_sampled(self, name):
        """Top-hat placeholders had ~20 points; measured curves have hundreds."""
        assert len(self._read(name)) > 100

    @pytest.mark.parametrize("name", FILTER_NAMES)
    def test_effective_wavelength(self, name):
        from astropy.io import ascii as ioascii
        qe = ioascii.read(MAVIS_DIR / "QE_mavis_ccd.dat")
        qe_wave = np.asarray(qe["wavelength"], dtype=float)
        qe_trans = np.asarray(qe["transmission"], dtype=float)

        tbl = self._read(name)
        wave = np.asarray(tbl["wavelength"], dtype=float)
        trans = np.asarray(tbl["transmission"], dtype=float)
        resp = trans * np.interp(wave, qe_wave, qe_trans, left=0.0, right=0.0)

        lam_eff = float(trapezoid(wave * resp, wave)
                        / trapezoid(resp, wave))
        expected = FILTER_LAM_EFF[name]
        assert lam_eff == pytest.approx(expected, abs=LAM_EFF_TOL), \
            f"{name}: lambda_eff {lam_eff:.4f} um, expected {expected} um"

    @pytest.mark.parametrize("name", FILTER_NAMES)
    def test_provenance_is_recorded(self, name):
        head = (MAVIS_DIR / "filters" / f"TC_filter_{name}.dat").read_text(
            encoding="utf-8")[:1500]
        assert "SVO Filter Profile Service" in head
        assert "source_components : Filter" in head, \
            f"{name}: profile must be filter-only, QE is applied separately"


# ---------------------------------------------------------------------------
# Atmosphere
# ---------------------------------------------------------------------------

@pytest.mark.webtest
class TestAtmosphere:
    """MAVIS works in the visible; the Paranal package was set up for the NIR.

    The only enabled atmosphere effect in Paranal.yaml is SkycalcTERCurve,
    whose grid runs 3200.0 - 9999.66 Angstrom. The MAVIS SIM wavelength range
    has to stay inside that, or the band edges silently get zero transmission.
    """

    @pytest.fixture(scope="class")
    def atmo(self):
        cmd = scopesim.UserCommands(use_instrument="MAVIS")
        opt = scopesim.OpticalTrain(cmd)
        effect = opt["skycalc_atmosphere"]
        return effect[0] if isinstance(effect, list) else effect

    def test_band_edges_still_transmit(self, atmo):
        """The whole requested range must carry real atmospheric transmission.

        Sampled just inside the edges on purpose. SkycalcTERCurve returns a
        grid whose last point sits a fraction of a step short of the requested
        ``wave_max``, so evaluating exactly at ``wave_max`` extrapolates to
        zero. That is generic ScopeSim behaviour and moving the range does not
        avoid it; it costs the last ~0.3 Angstrom of the band.
        """
        cmd = scopesim.UserCommands(use_instrument="MAVIS")
        wave_min = float(cmd["!SIM.spectral.wave_min"])
        wave_max = float(cmd["!SIM.spectral.wave_max"])
        margin = 1e-3   # [um]

        for edge in (wave_min + margin, wave_max - margin):
            trans = float(atmo.throughput(edge * u.um))
            assert trans > 0.05, \
                f"atmospheric transmission at {edge:.4f} um is {trans:.4f}"

    @pytest.mark.parametrize("wave, lo, hi", [
        (0.35, 0.35, 0.70),   # ozone + Rayleigh still biting hard
        (0.55, 0.75, 0.95),
        (0.90, 0.90, 1.00),
    ])
    def test_transmission_is_physical(self, atmo, wave, lo, hi):
        trans = float(atmo.throughput(wave * u.um))
        assert lo <= trans <= hi, \
            f"atmospheric transmission at {wave} um is {trans:.3f}"

    def test_transmission_rises_towards_the_red(self, atmo):
        waves = [0.35, 0.45, 0.55, 0.70, 0.90]
        trans = [float(atmo.throughput(w * u.um)) for w in waves]
        assert all(b > a for a, b in zip(trans, trans[1:])), trans

    def test_no_zero_transmission_inside_the_band(self, atmo):
        """Guards the wave_max regression: 1.00 um used to return exactly 0."""
        waves = np.linspace(0.34, 0.98, 60)
        trans = np.array([float(atmo.throughput(w * u.um)) for w in waves])
        assert (trans > 0.05).all(), \
            f"zero/near-zero transmission at {waves[trans <= 0.05]}"


# ---------------------------------------------------------------------------
# Radiometry
# ---------------------------------------------------------------------------

# VLT UT4 collecting area from VLT/LIST_VLT_mirrors.dat: 8.2 m outer diameter
# with a 1.0 m central obstruction.
TEL_AREA_CM2 = np.pi * ((820.0 / 2) ** 2 - (100.0 / 2) ** 2)

PIXEL_SCALE = 0.00736     # [arcsec/pix]

# Vega zero point at 5500 Angstrom
F0_V = 3.63e-9             # [erg/s/cm2/Angstrom] for V = 0
HC = 6.626e-27 * 2.998e10  # [erg cm]


def _photon_energy(wave_angstrom):
    """Photon energy in erg."""
    return HC / (wave_angstrom * 1e-8)


def _system_transmission(opt, wave_angstrom, with_atmosphere):
    """System throughput on a wavelength grid, atmosphere in or out.

    Note that passing "!ATMO.skycalc_atmosphere.include" through
    UserCommands(properties=...) does *not* switch the effect off; it has to
    be done on the built train.
    """
    atmo = opt["skycalc_atmosphere"]
    atmo = atmo[0] if isinstance(atmo, list) else atmo
    atmo.include = with_atmosphere
    opt.update()
    curve = opt.optics_manager.system_transmission(plot=False)
    return np.asarray(curve((wave_angstrom * u.AA).to(u.um)).value, dtype=float)


@pytest.mark.slow
@pytest.mark.webtest
class TestRadiometry:
    """Photon bookkeeping, checked end to end against hand integration."""

    WAVE = np.linspace(4500.0, 7000.0, 2501)   # [Angstrom], brackets V

    @pytest.fixture(scope="class")
    def train(self):
        cmd = scopesim.UserCommands(
            use_instrument="MAVIS",
            properties={"!OBS.filter_name": "V", "!OBS.dit": 60,
                        "!OBS.ndit": 1},
        )
        return scopesim.OpticalTrain(cmd)

    @pytest.fixture(scope="class")
    def measured_sky(self):
        """Sky level from an empty-sky readout, in e-/s/arcsec2."""
        from scopesim.source import source_templates as st
        cmd = scopesim.UserCommands(
            use_instrument="MAVIS",
            properties={"!OBS.filter_name": "V", "!OBS.dit": 60,
                        "!OBS.ndit": 1},
        )
        opt = scopesim.OpticalTrain(cmd)
        opt.observe(st.empty_sky(), update=True)
        img = opt.readout()[0][1].data.astype(float)
        # gain is 1.0 ADU/e-, so ADU == electrons here
        return float(np.median(img)) / 60.0 / PIXEL_SCALE ** 2

    def test_effects_are_not_applied_twice(self, train):
        """Guards against listing a yaml in both the base and a mode list.

        That duplicates every optical element, so each transmission curve is
        applied twice and the system throughput comes out squared.
        """
        rows = [(el.meta.get("name"), eff.display_name)
                for el in train.optics_manager.optical_elements
                for eff in el.effects]
        assert len(rows) == len(set(rows)), \
            f"duplicated effects: {sorted(r for r in rows if rows.count(r) > 1)}"

    def test_system_throughput_is_plausible(self, train):
        """Peak V-band throughput, atmosphere included.

        VLT mirrors (0.77) x AO module (0.63) x V filter (0.83) x QE (0.89)
        x atmosphere (0.86) is about 0.31.
        """
        tp = _system_transmission(train, np.linspace(4500.0, 6500.0, 401),
                                  with_atmosphere=True)
        assert 0.20 < tp.max() < 0.40, f"peak throughput is {tp.max():.3f}"

    def test_signal_scales_with_dit_and_ndit(self):
        """Regression guard: ExposureIntegration was once commented out, so
        the readout returned a per-second image and DIT did nothing."""
        from scopesim.source import source_templates as st
        levels = {}
        for dit, ndit in ((60.0, 1), (120.0, 1), (60.0, 2)):
            cmd = scopesim.UserCommands(
                use_instrument="MAVIS",
                properties={"!OBS.filter_name": "V", "!OBS.dit": dit,
                            "!OBS.ndit": ndit},
            )
            opt = scopesim.OpticalTrain(cmd)
            opt.observe(st.empty_sky(), update=True)
            levels[(dit, ndit)] = float(
                np.median(opt.readout()[0][1].data.astype(float)))

        base = levels[(60.0, 1)]
        assert levels[(120.0, 1)] == pytest.approx(2 * base, rel=0.05)
        assert levels[(60.0, 2)] == pytest.approx(2 * base, rel=0.05)

    def test_sky_level_matches_hand_integrated_skycalc(
            self, train, measured_sky, report):
        """The readout must reproduce a hand integration of the sky spectrum.

        This checks the photon bookkeeping of the whole chain -- emission,
        collecting area, throughput, QE, integration time, gain -- against
        the same quantities integrated directly. Sky photons are emitted by
        the atmosphere, so they are not attenuated by it.
        """
        atmo = train["skycalc_atmosphere"]
        atmo = atmo[0] if isinstance(atmo, list) else atmo
        em = np.asarray(atmo.surface.emission(self.WAVE * u.AA).value,
                        dtype=float)

        tp = _system_transmission(train, self.WAVE, with_atmosphere=False)
        expected = float(trapezoid(em * tp, self.WAVE)) * TEL_AREA_CM2

        report.background["V"] = {"measured": measured_sky,
                                  "expected": expected}

        assert measured_sky == pytest.approx(expected, rel=0.10), (
            f"sky {measured_sky:.0f} e-/s/arcsec2 vs hand-integrated "
            f"{expected:.0f} e-/s/arcsec2"
        )

    def test_sky_brightness_is_plausible_for_paranal(self, train, measured_sky):
        """The implied V surface brightness must look like a real sky.

        skycalc is queried with its default moon and airglow settings, which
        are not dark time, so this comes out brighter than the canonical
        21.6 mag/arcsec2 dark-sky value.
        """
        tp = _system_transmission(train, self.WAVE, with_atmosphere=False)
        # e-/s/arcsec2 that a V = 0 mag/arcsec2 surface would produce
        zp = float(trapezoid(
            F0_V / _photon_energy(self.WAVE) * tp, self.WAVE)) * TEL_AREA_CM2
        sky_mag = -2.5 * np.log10(measured_sky / zp)

        assert 19.0 < sky_mag < 22.5, (
            f"implied V sky brightness {sky_mag:.2f} mag/arcsec2 is not a "
            "plausible Paranal sky"
        )

    def test_point_source_sensitivity(self, train, report):
        """Limiting magnitude, against the published V > 29 (5 sigma, 1 hr).

        Measured in a 50 mas aperture, the box the ensquared-energy
        specification refers to. The published figure assumes optimal
        PSF-weighted extraction and dark time, so an aperture measurement
        against the brighter skycalc default sky is expected to land a
        magnitude or so brighter.
        """
        from astropy.io import fits

        with fits.open(MAVIS_DIR / "PSF_MAVIS_mcao.fits") as hdul:
            ee50 = {h.header["WAVE0"]: h.header["EE50MAS"]
                    for h in hdul[1:]}[0.55]

        # 1 hr split into 300 s DITs keeps read noise sub-dominant
        dit, ndit = 300.0, 12
        exptime = dit * ndit
        box = 0.050                                     # [arcsec]
        npix = (box / PIXEL_SCALE) ** 2

        # a point source is seen through the atmosphere, the sky is not
        tp_src = _system_transmission(train, self.WAVE, with_atmosphere=True)
        zp_rate = float(trapezoid(
            F0_V / _photon_energy(self.WAVE) * tp_src, self.WAVE)) \
            * TEL_AREA_CM2

        atmo = train["skycalc_atmosphere"]
        atmo = atmo[0] if isinstance(atmo, list) else atmo
        em = np.asarray(atmo.surface.emission(self.WAVE * u.AA).value,
                        dtype=float)
        tp_sky = _system_transmission(train, self.WAVE, with_atmosphere=False)
        sky_rate = float(trapezoid(em * tp_sky, self.WAVE)) \
            * TEL_AREA_CM2 * box ** 2

        background = (sky_rate * exptime
                      + 0.001 * exptime * npix          # dark current
                      + 3.0 ** 2 * npix * ndit)         # read noise

        mags = np.linspace(22.0, 32.0, 401)
        source = zp_rate * 10 ** (-0.4 * mags) * exptime * ee50
        snrs = source / np.sqrt(source + background)
        lim_mag = float(np.interp(-5.0, -snrs, mags))

        report.lim_mag["V"] = {"mags": mags, "snrs": snrs,
                               "limiting_mag": lim_mag,
                               "exptime": exptime, "snr": 5.0,
                               "aperture_mas": 50.0}

        assert 26.0 < lim_mag < 30.0, (
            f"5-sigma limiting magnitude in 1 hr is V = {lim_mag:.2f}, "
            "which is not consistent with the published V > 29"
        )
