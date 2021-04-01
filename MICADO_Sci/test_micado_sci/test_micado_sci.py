from os import path as pth

import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt

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
        assert isinstance(opt, sim.OpticalTrain)
        print(opt)

    def test_makes_scao_1_5mas_optical_train(self):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["SCAO", "1.5mas"])
        opt = sim.OpticalTrain(cmd)
        print(opt)


class TestObserve:
    def observe_with_micado_sci(self, modes):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=modes)

        opt = sim.OpticalTrain(cmd)
        src = sim.source.source_templates.empty_sky()

        opt.observe(src)
        hdus = opt.readout()

        return hdus

    def test_empty_sky_with_mcao_4mas(self):
        hdus = self.observe_with_micado_sci(modes=["MCAO", "IMG_4mas"])
        im = hdus[0][1].data

        assert im.shape == (4096, 4096)
        assert np.median(im) > 0

        if PLOTS:
            plt.imshow(im)
            plt.show()

    def test_scao_1_5mas_works(self):
        hdus = self.observe_with_micado_sci(modes=["SCAO", "IMG_1.5mas"])
        im = hdus[0][1].data

        assert im.shape == (4096, 4096)
        assert np.median(im) > 0

        if PLOTS:
            plt.imshow(im)
            plt.show()


def test_spec_for_a_specific_wavelength_range_works():
    pass





