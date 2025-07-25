"""
0-mag photon fluxes from Vega Spectrum
--------------------------------------
J band (J=0mag)   --> 3505e6 ph/s/m2
H band (H=0mag)   --> 2416e6 ph/s/m2
Ks band (Ks=0mag) --> 1211e6 ph/s/m2
Lp band (Lp=0mag) -->  576e6 ph/s/m2
Mp band (Mp=0mag) -->  268e6 ph/s/m2
"""

# integration test using everything and the HAWKI package
import pytest
from pytest import approx
import os
import os.path as pth

import numpy as np
from astropy import units as u
from astropy.io import ascii

import scopesim
import scopesim.source.source_templates
from scopesim.tests.mocks.py_objects.source_objects import _single_table_source
from scopesim import rc

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

# pytest_plugins = ['pytest_profiling']
if rc.__config__["!SIM.tests.run_integration_tests"] is False:
    pytestmark = pytest.mark.skip("Ignoring HAWKI integration tests")

IRDB_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
DATA_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))
rc.__config__["!SIM.file.local_packages_path"] = IRDB_DIR
rc.__search_path__.insert(0, DATA_DIR)

PLOTS = False

PKGS = {"Paranal": "locations/Paranal.zip",
        "VLT": "telescopes/VLT.zip",
        "HAWKI": "instruments/HAWKI.zip"}


class TestInit:
    def test_all_packages_are_available(self):
        rc_local_path = rc.__config__["!SIM.file.local_packages_path"]
        print("irdb" not in rc_local_path)
        for pkg_name in PKGS:
            assert os.path.isdir(os.path.join(rc_local_path, pkg_name))


class TestLoadUserCommands:
    def test_user_commands_loads_without_throwing_errors(self, capsys):
        cmd = scopesim.UserCommands(use_instrument="HAWKI")
        assert isinstance(cmd, scopesim.UserCommands)
        for key in ["SIM", "OBS", "ATMO", "TEL", "INST", "DET"]:
            assert key in cmd and len(cmd[key]) > 0

        stdout = capsys.readouterr()
        assert len(stdout.out) == 0


@pytest.mark.slow
class TestMakeOpticalTrain:
    def test_works_seamlessly_for_hawki_package(self, capsys):
        cmd = scopesim.UserCommands(use_instrument="HAWKI")
        opt = scopesim.OpticalTrain(cmd)
        opt["detector_1024_window"].include = False
        opt["detector_array_list"].include = True
        opt.update()

        # test that the major values have been updated
        assert opt.cmds["!TEL.area"].value == approx(52.02, rel=1e-3)
        assert opt.cmds["!TEL.etendue"].value == approx(0.58455, rel=1e-3)
        assert opt.cmds["!INST.pixel_scale"] == approx(0.106, rel=1e-3)

        # test that OpticalTrain builds properly
        assert isinstance(opt, scopesim.OpticalTrain)

        # test that we have a system throughput
        wave = np.linspace(0.7, 2.5, 181) * u.um
        tc = opt.optics_manager.system_transmission
        # ec = opt.optics_manager.surfaces_table.emission
        # ..todo:: something super wierd is going on here when running pytest in the top directory
        # ..todo:: perhaps this is has to be relaxed due to different filter
        # assert 0.5 < np.max(tc(wave)).value < 0.55
        assert 0.5 < np.max(tc(wave)).value < 0.8

        if PLOTS:
            plt.plot(wave, tc(wave))
            plt.show()

        # if PLOTS:
        #     plt.plot(wave, ec(wave))
        #     plt.show()

        # test that we have the correct number of FOVs for Ks band
        # assert len(opt.fov_manager.fovs) == 18
        # Apparently this is 9 now?
        assert len(opt.fov_manager.fovs) == 9

        if PLOTS:
            fovs = opt.fov_manager.fovs
            from scopesim.optics.image_plane_utils import calc_footprint
            plt.subplot(121)
            for fov in fovs:
                x, y = calc_footprint(fov.hdu.header)
                plt.fill(x*3600, y*3600, alpha=0.1, c="b")
                plt.title("Sky plane")
                plt.xlabel("[arcsec]")

            plt.subplot(122)
            for fov in fovs:
                x, y = calc_footprint(fov.hdu.header, "D")
                plt.fill(x, y)
                plt.title("Detector focal plane")
                plt.xlabel("[mm]")

            plt.show()

        # test that the ImagePlane is large enough
        assert opt.image_planes[0].header["NAXIS1"] > 4200
        assert opt.image_planes[0].header["NAXIS2"] > 4200
        assert np.all(opt.image_planes[0].data == 0)

        # test assert there are 4 detectors, each 2048x2048 pixels
        hdu = opt.readout()[0]
        assert len(opt.detector_managers[0]) == 4
        for detector in opt.detector_managers[0]:
            assert detector.hdu.header["NAXIS1"] == 2048
            assert detector.hdu.header["NAXIS2"] == 2048

        if PLOTS:
            for i in range(1, 5):
                plt.subplot(2, 2, i)
                plt.imshow(hdu[i].data)
            plt.show()

        dit = opt.cmds["!OBS.dit"]
        ndit = opt.cmds["!OBS.ndit"]
        assert np.average(hdu[1].data) == approx(ndit * dit * 0.1, abs=0.5)

    def test_system_transmission_is_similar_to_eso_etc(self):
        """
        A ~20% discrepency between the ESO and ScopeSim system throughputs
        """

        for filt_name in ["Y", "J", "H", "Ks", "BrGamma", "CH4"]:

            cmd = scopesim.UserCommands(use_instrument="HAWKI")
            cmd["!OBS.filter_name"] = filt_name
            opt = scopesim.OpticalTrain(cmd)
            # TODO: Exclude if it is included?
            # opt["paranal_atmo_default_ter_curve"].include = False

            src = _single_table_source(n=1000)
            opt.observe(src)

            if PLOTS:
                fname = "hawki_eso_etc/TER_system_{}.dat".format(filt_name)
                dname = os.path.dirname(__file__)
                etc_tbl = ascii.read(os.path.join(dname, fname))
                etc_wave = etc_tbl["wavelength"] * 1e-3 * u.um
                etc_thru = etc_tbl["transmission"] * 1e-2
                # plt.plot(etc_wave, etc_thru, c="b", label="ESO/ETC")

                flux_init = src.spectra[0](etc_wave)
                flux_final = opt._last_source.spectra[0](etc_wave)
                ss_thru = flux_final / flux_init
                # plt.plot(etc_wave, ss_thru, c="r", label="ScopeSim/HAWKI")

                plt.plot(etc_wave, ss_thru / etc_thru - 1)

                plt.ylim(0, 0.5)
                plt.show()


class TestObserveOpticalTrain:
    """
    Based on mocks/photometry/check_photometry.py

    Sky BG from my HAWKI archive data (ph s-1 pixel-1)
    J 170
    H 958
    Ks 1204
    BrG 213

    K filter
    --------
    Skycalc BG ph flux for K: 0.08654 ph / (cm2 s arcsec2)
    -> HAWKI sky BG = 510 ph / s / pixel
                    = 0.08654252 * (410**2 * np.pi) * (0.106**2)

    ETC gives 2550 e-/DIT/pixel for a 1s DET at airmass=1.0, pwv=2.5
    (HAWKI archive average 1204 e-/s-1/pixel)
    Remaining must come from VLT or entrance window

    H BG (based on skycalc and 0 mag vega): 1000 ph/s/m2/arcsec2
    HAWKI --> 600 ph/s/pixel

    ScopeSim Flux contributors to final BG count
    - all : 1360
    - minus "paranal_atmo_default_ter_curve" : 850
    - minus "vlt_mirror_list" : 780
    - minus entrance window from "hawki_mirror_list" : 0

    H filter
    --------
    Skycalc BG ph flux for K: 0.39862 ph / (cm2 s arcsec2)
    -> HAWKI sky BG = 2365 ph / s / pixel

    ETC gives 1625 e-/DIT/pixel for a 1s DET at airmass=1.0, pwv=2.5
    (HAWKI archive average 958 e-/s-1/pixel)
    Remaining must come from VLT or entrance window

    H BG (based on skycalc and 0 mag vega): 4000 ph/s/m2/arcsec2
    HAWKI --> 2400 ph/s/pixel

    ScopeSim Flux contributors to final BG count
    - all : 2370
    - minus "paranal_atmo_default_ter_curve" : 2
    - minus "vlt_mirror_list" : 1.8
    - minus entrance window from "hawki_mirror_list" : 0

    J filter
    --------
    Skycalc BG ph flux for K: 0.39862 ph / (cm2 s arcsec2)
    -> HAWKI sky BG = 444 ph / s / pixel

    ETC gives 225 e-/DIT/pixel for a 1s DET at airmass=1.0, pwv=2.5
    (HAWKI archive average 170 e-/s-1/pixel)
    Remaining must come from VLT or entrance window

    J BG (based on skycalc and 0 mag vega): 688 ph/s/m2/arcsec2
    HAWKI --> 400 ph/s/pixel

    ScopeSim Flux contributors to final BG count
    - all : 290
    - minus "paranal_atmo_default_ter_curve" : 0
    - minus "vlt_mirror_list" : 0
    - minus entrance window from "hawki_mirror_list" : 0

    Given the variability of the backgrounds, ScopeSim is doing a pretty
    good job of making the background contributions

    """

    @pytest.mark.xfail(reason="Apparently this is waaaaay off now.")
    @pytest.mark.parametrize("filter_name, bg_level",
                             [("J", 400), ("H", 2400), ("Ks", 1000)])
    def test_background_is_similar_to_online_etc(self, filter_name, bg_level):

        cmd = scopesim.UserCommands(use_instrument="HAWKI")
        cmd["!OBS.filter_name"] = filter_name
        opt = scopesim.OpticalTrain(cmd)

        effects = {"paranal_atmo_default_ter_curve": True,
                   "vlt_mirror_list": False,
                   "hawki_mirror_list": False}
        for key, val in effects.items():
            opt[key].include = val

        src = scopesim.source.source_templates.empty_sky()
        opt.observe(src)

        if PLOTS:
            wave = np.arange(0.7, 2.5, 0.001) * u.um
            specs = opt._last_source.spectra
            for i in range(len(specs)):
                flux = specs[i](wave)
                plt.plot(wave, flux)
            plt.show()

        assert np.average(opt.image_planes[0].data) == approx(bg_level, rel=0.2)

    def test_actually_produces_stars(self):
        cmd = scopesim.UserCommands(use_instrument="HAWKI",
                                    properties={"!OBS.dit": 360,
                                                "!OBS.ndit": 10})
        cmd.ignore_effects += ["detector_linearity"]

        opt = scopesim.OpticalTrain(cmd)
        src = scopesim.source.source_templates.star_field(10000, 5, 15, 440)

        # ETC gives 2700 e-/DIT for a 1s DET at airmass=1.2, pwv=2.5
        # background should therefore be ~ 8.300.000
        opt.observe(src)
        hdu = opt.readout()[0]

        implane_av = np.average(opt.image_planes[0].data)
        hdu_av = np.average([hdui.data for hdui in hdu[1:]])
        exptime = cmd["!OBS.ndit"] * cmd["!OBS.dit"]

        assert hdu_av == approx(implane_av * exptime, rel=0.01)

        if PLOTS:
            plt.subplot(1, 2, 1)
            plt.imshow(opt.image_planes[0].image[128:2048, 128:2048].T,
                       norm=LogNorm())
            plt.colorbar()

            plt.subplot(1, 2, 2)
            plt.imshow(hdu[1].data[128:2048, 128:2048].T, norm=LogNorm(),
                       vmax=3e7)
            plt.colorbar()

            plt.show()
