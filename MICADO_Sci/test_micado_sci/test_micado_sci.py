import pytest
from os import path as pth

import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import scopesim as sim
from scopesim import rc

pytest.skip(allow_module_level=True)

TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH

PLOTS = False


class TestUserCommands:
    def test_reads_in_default_yaml(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci")
        isinstance(cmd, sim.UserCommands)

    def test_throws_error_if_wrong_mode_names_passed(self):
        with pytest.raises(ValueError):
            sim.UserCommands(use_instrument="MICADO_Sci", set_modes=["DODGY_MODE_NAME"])

    def test_elt_ter_curve_reads_in(self):
        filename = pth.join(TOP_PATH, "ELT", "TER_ELT_System_20190611.dat")
        elt = sim.effects.TERCurve(filename=filename)

        if PLOTS:
            wave = np.arange(0.3, 2.5, 0.001) * u.um
            plt.plot(wave, elt.surface.reflection(wave))
            plt.show()

        assert isinstance(elt, sim.effects.TERCurve)


class TestOpticalTrain:
    def test_makes_mcao_4mas_optical_train(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["MCAO", "IMG_4mas"])
        opt = sim.OpticalTrain(cmd)
        print(opt)
        assert isinstance(opt, sim.OpticalTrain)

    def test_makes_scao_1_5mas_optical_train(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["SCAO", "IMG_1.5mas"])
        opt = sim.OpticalTrain(cmd)
        print(opt)
        assert isinstance(opt, sim.OpticalTrain)

    def test_makes_spec_3000x50_optical_train(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["SPEC"])
        opt = sim.OpticalTrain(cmd)
        print(opt)
        assert isinstance(opt, sim.OpticalTrain)


class TestObserve:
    def test_grid_with_scao_4mas(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["SCAO", "IMG_4mas"])
        cmd["!OBS.dit"] = 3600
        cmd["!OBS.ndit"] = 5

        opt = sim.OpticalTrain(cmd)
        src = sim.source.source_templates.star_field(100, 20, 30, 3, use_grid=True)
        opt.observe(src)
        hdus = opt.readout()
        im = hdus[0][1].data

        assert im.shape == (1024, 1024)
        assert np.median(im) > 0

        sys_trans = opt.optics_manager.system_transmission
        effects = opt.optics_manager.get_z_order_effects(100)

        for effect in effects:
            print(effect)

        if PLOTS:
            plt.subplot(121)
            wave = np.linspace(0.5, 2.5, 1000) * u.um
            plt.plot(wave, sys_trans(wave))

            plt.subplot(122)
            im = opt.image_planes[0].image
            plt.imshow(im, norm=LogNorm(),
                       vmin=0.99*np.average(im), vmax=1.1*np.average(im))
            plt.show()

    def test_star_field_with_mcao_4mas(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["SCAO", "IMG_4mas"])
        opt = sim.OpticalTrain(cmd)

        src = sim.source.source_templates.star_field(100, 20, 30, 3, use_grid=True)
        opt.observe(src)
        hdus = opt.readout()
        im = hdus[0][1].data

        assert im.shape == (1024, 1024)
        assert np.median(im) > 0

        if PLOTS:
            plt.imshow(opt.image_planes[0].image, norm=LogNorm())
            plt.show()

    @pytest.mark.skip(reason="Takes too much memory, can get killed by OOM killer in ScopeSIM 0.4.0. Works in 0.1.4.")
    def test_star_field_with_spec(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["MCAO", "SPEC"])
        opt = sim.OpticalTrain(cmd)

        src = sim.source.source_templates.star_field(100, 20, 30, 3, use_grid=True)
        opt.observe(src)

        if PLOTS:
            plt.imshow(opt.image_planes[0].image, norm=LogNorm())
            plt.show()

    @pytest.mark.skip(reason="Takes too much memory, can get killed by OOM killer in ScopeSIM 0.4.0. Works in 0.1.4.")
    def test_spec_for_a_specific_wavelength_range_works(self):
        n = 11
        src = sim.source.source_templates.star_field(n, 15, 25, 3, use_grid=False)
        src.fields[0]["x"] = np.linspace(-1.5, 1.5, n)
        src.fields[0]["y"] = [0] * n
        # src needs to be shifted to prevent an error from astropy.units:
        # "TypeError: None is not a valid Unit
        src.shift()
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["SCAO", "SPEC"])
        cmd["!OBS.dit"] = 3600                  # sec
        cmd["!SIM.spectral.wave_mid"] = 1.95    # um
        cmd["!INST.aperture.width"] = 3         # arcsec
        cmd["!INST.aperture.height"] = 0.05     # arcsec
        cmd["!DET.width"] = int((cmd["!INST.aperture.width"] / 0.004) * 1.1)    # pixel
        cmd["!DET.height"] = 128              # pixel

        opt = sim.OpticalTrain(cmd)
        opt.observe(src)
        hdu = opt.readout()[0]
        # hdu.writeto("spec_scao_massive.TEST.fits", overwrite=True)

        if PLOTS:
            plt.imshow(hdu[1].data, norm=LogNorm())
            plt.show()

