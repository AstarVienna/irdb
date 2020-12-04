
from os import path as pth

import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import scopesim as sim
from scopesim import rc

TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH

PLOTS = False


def test_elt_ter_curve_reads_in():
    filename = pth.join(TOP_PATH, "ELT", "TER_ELT_System_20190611.dat")
    elt = sim.effects.TERCurve(filename=filename)

    if PLOTS:
        wave = np.arange(0.3, 2.5, 0.001) * u.um
        plt.plot(wave, elt.surface.reflection(wave))
        plt.show()

    assert isinstance(elt, sim.effects.TERCurve)


class TestUserCommands:
    def test_reads_in_default_yaml(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci")
        isinstance(cmd, sim.UserCommands)


class TestOpticalTrain:
    def test_makes_mcao_4mas_optical_train(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["MCAO", "4mas"])
        opt = sim.OpticalTrain(cmd)
        print(opt)
        assert isinstance(opt, sim.OpticalTrain)

    def test_makes_scao_1_5mas_optical_train(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["SCAO", "1.5mas"])
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
                               set_modes=["SCAO", "4mas"])
        cmd["!OBS.dit"] = 3600
        cmd["!OBS.ndit"] = 5

        opt = sim.OpticalTrain(cmd)
        src = sim.source.source_templates.star_field(100, 20, 30, 3, use_grid=True)
        opt.observe(src)
        hdu = opt.readout()[0]

        im = opt.image_planes[0].image
        im = hdu[1].data

        sys_trans = opt.optics_manager.system_transmission
        effects = opt.optics_manager.get_z_order_effects(100)

        for effect in effects:
            print(effect)

        if PLOTS:
            plt.subplot(121)
            wave = np.linspace(0.5, 2.5, 1000) * u.um
            plt.plot(wave, sys_trans(wave))

            plt.subplot(122)
            plt.imshow(im, norm=LogNorm(),
                       vmin=0.99*np.average(im), vmax=1.1*np.average(im))
            plt.show()


def test_spec_for_a_specific_wavelength_range_works():
    n = 11
    src = sim.source.source_templates.star_field(n, 15, 25, 3, use_grid=False)
    src.fields[0]["x"] = np.linspace(-1.5, 1.5, n)
    src.fields[0]["y"] = [0] * n
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

