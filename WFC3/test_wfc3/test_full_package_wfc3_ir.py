# integration test using everything and the HAWKI package
import pytest
from pytest import approx
import os
from os import path as pth

import numpy as np
from astropy import units as u

import scopesim
import scopesim.source.source_templates
from scopesim import rc

from matplotlib import pyplot as plt

if rc.__config__["!SIM.tests.run_integration_tests"] is False:
    pytestmark = pytest.mark.skip("Ignoring WFC3 integration tests")

TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH

PKGS = {"HST": "telescopes/HST.zip",
        "WFC3": "instruments/WFC3.zip"}

PLOTS = False


class TestInit:
    def test_all_packages_are_available(self):
        rc_local_path = rc.__config__["!SIM.file.local_packages_path"]
        print("irdb" not in rc_local_path)
        for pkg_name in PKGS:
            assert os.path.isdir(os.path.join(rc_local_path, pkg_name))


class TestLoadUserCommands:
    def test_user_commands_loads_without_throwing_errors(self, capsys):
        cmd = scopesim.UserCommands(use_instrument="WFC3")
        assert isinstance(cmd, scopesim.UserCommands)
        for key in ["SIM", "OBS", "TEL", "INST", "DET"]:
            assert key in cmd and len(cmd[key]) > 0

        stdout = capsys.readouterr()
        assert len(stdout.out) == 0


class TestMakeOpticalTrain:
    def test_works_seamlessly_for_wfc3_package(self, capsys):
        cmd = scopesim.UserCommands(use_instrument="WFC3")
        opt = scopesim.OpticalTrain(cmd)

        # test that the major values have been updated
        assert opt.cmds["!TEL.area"].value == approx(4.453, rel=1e-3)
        assert opt.cmds["!TEL.etendue"].value == approx(0.0753, rel=1e-3)
        assert opt.cmds["!INST.pixel_scale"] == approx(0.13, rel=1e-3)

        # test that OpticalTrain builds properly
        assert isinstance(opt, scopesim.OpticalTrain)

        # test that we have a system throughput
        wave = np.linspace(0.7, 1.8, 111) * u.um
        tc = opt.optics_manager.system_transmission
        # ec = opt.optics_manager.surfaces_table.emission
        # ..todo:: something super wierd is going on here when running pytest in the top directory
        assert 0.4 < np.max(tc(wave)) < 0.6

        if PLOTS:
            plt.plot(wave, tc(wave))
            plt.show()

        # if PLOTS:
        #     plt.plot(wave, ec(wave))
        #     plt.show()

        # test that we have the correct number of FOVs for Ks band
        assert len(opt.fov_manager.fovs) == 1

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
        # Note: This was "> 1024", which failed after the off-by-one fix.
        #       Is there any physical reason why 1024 exactly is not enough?
        assert opt.image_planes[0].header["NAXIS1"] >= 1024
        assert opt.image_planes[0].header["NAXIS2"] >= 1024
        assert np.all(opt.image_planes[0].data == 0)

        # test assert there are 1 detector
        hdu = opt.readout()[0]
        assert len(opt.detector_managers[0]) == 1
        for detector in opt.detector_managers[0]:
            assert detector.hdu.header["NAXIS1"] == 1024
            assert detector.hdu.header["NAXIS2"] == 1024

        if PLOTS:
            plt.imshow(hdu[0].data)
            plt.show()

        dit = opt.cmds["!OBS.dit"]
        ndit = opt.cmds["!OBS.ndit"]
        assert np.average(hdu[1].data) == approx(ndit * dit * 0.048, abs=1)


class TestObserveOpticalTrain:
    @pytest.mark.xfail(reason="This is off now.")
    def test_background_is_similar_to_online_etc(self):
        cmd = scopesim.UserCommands(use_instrument="WFC3")
        opt = scopesim.OpticalTrain(cmd)
        src = scopesim.source.source_templates.empty_sky()

        # ..todo:: Don't know what the real HST background is
        opt.observe(src)
        print("HELLO", np.average(opt.image_planes[0].data))
        assert np.average(opt.image_planes[0].data) == approx(0.11, rel=0.2)

    def test_actually_produces_stars(self):
        cmd = scopesim.UserCommands(use_instrument="WFC3",
                                    properties={"!OBS.dit": 1,
                                                "!OBS.ndit": 1})
        cmd.ignore_effects += ["detector_linearity"]

        opt = scopesim.OpticalTrain(cmd)
        src = scopesim.source.source_templates.star_field(10000, 10, 10, 150, use_grid=True)

        opt.observe(src)
        hdu = opt.readout()[0]

        implane_av = np.average(opt.image_planes[0].data)
        hdu_av = np.average(hdu[1].data)
        exptime = cmd["!OBS.ndit"] * cmd["!OBS.dit"]

        if PLOTS:
            plt.subplot(1, 2, 1)
            plt.imshow(opt.image_planes[0].image, norm="log", origin="lower",
                       vmin=np.median(opt.image_planes[0].image))
            plt.colorbar()

            plt.subplot(1, 2, 2)
            plt.imshow(hdu[1].data, norm="log", origin="lower",
                       vmin=np.median(hdu[1].data))
            plt.colorbar()

            plt.show()

        assert hdu_av == approx(implane_av * exptime, rel=0.015)
