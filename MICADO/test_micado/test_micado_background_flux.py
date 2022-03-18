# integration test using everything and the MICADO package
import pytest
from pytest import approx
import os
import os.path as pth
import shutil

import numpy as np
from astropy import units as u
from astropy.io import fits

import scopesim as sim
from scopesim import rc
from scopesim.source.source_templates import empty_sky

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm


TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH


class TestInit:
    @pytest.mark.parametrize("modes", [["SCAO", "IMG_4mas"],
                                       ["SCAO", "IMG_1.5mas"],
                                       ["MCAO", "IMG_4mas"],
                                       ["MCAO", "IMG_1.5mas"]])
    def test_micado_loads_optical_train(self, modes):
        cmds = sim.UserCommands(use_instrument="MICADO", set_modes=modes)
        micado = sim.OpticalTrain(cmds)
        opt_els = np.unique(micado.effects["element"])

        assert isinstance(micado, sim.OpticalTrain)
        assert len(opt_els) == 6


class TestBackgroundLevels:
    """
    from Ric's excel doc 2018-04-03
    sky + instr. bkg [e-/pixel/s] for 4 mas mode::

        Z     J       H       Ks
        0.6	5.0	    28.4	78.7

    """
    @pytest.mark.parametrize("fw1, fw2, bg_flux",
                             [("J", "open", 5),
                              ("open", "H", 30),
                              ("open", "Ks", 79)])
    def test_bg_SCAO_IMG_4mas(self, fw1, fw2, bg_flux):
        cmds = sim.UserCommands(use_instrument="MICADO")
        micado = sim.OpticalTrain(cmds)

        micado["filter_wheel_1"].change_filter(fw1)
        micado["filter_wheel_2"].change_filter(fw2)

        src = empty_sky()
        micado.observe(src)
        implane = micado.image_planes[0].hdu.data       # e-/pixel/s

        assert np.median(implane) == approx(bg_flux, rel=0.3)

    @pytest.mark.parametrize("fw1, fw2, bg_flux",
                             [("J", "open", 5),
                              ("open", "H", 30),
                              ("open", "Ks", 79)])
    def test_bg_SCAO_IMG_1_5mas(self, fw1, fw2, bg_flux):
        """
        Pixel size is 0.14 of the 4mas version, hence fluxes are lower
        """
        bg_flux *= (1.5 / 4)**2

        cmds = sim.UserCommands(use_instrument="MICADO",
                                set_modes=["SCAO", "IMG_1.5mas"])
        micado = sim.OpticalTrain(cmds)

        micado["filter_wheel_1"].change_filter(fw1)
        micado["filter_wheel_2"].change_filter(fw2)

        src = empty_sky()
        micado.observe(src)
        implane = micado.image_planes[0].hdu.data       # e-/pixel/s

        assert np.median(implane) == approx(bg_flux, rel=0.3)

    @pytest.mark.parametrize("fw1, fw2, bg_flux",
                             [("J", "open", 5),
                              ("open", "H", 30),
                              ("open", "Ks", 79)])
    def test_bg_SCAO_IMG_4mas(self, fw1, fw2, bg_flux):
        cmds = sim.UserCommands(use_instrument="MICADO",
                                set_modes=["MCAO", "IMG_4mas"])
        micado = sim.OpticalTrain(cmds)

        micado["filter_wheel_1"].change_filter(fw1)
        micado["filter_wheel_2"].change_filter(fw2)

        src = empty_sky()
        micado.observe(src)
        implane = micado.image_planes[0].hdu.data       # e-/pixel/s

        assert np.median(implane) == approx(bg_flux, rel=0.3)
