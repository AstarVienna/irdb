import pytest
from os import path as pth
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

from astropy import units as u

import scopesim as sim
import scopesim.source.source_templates as st

IRDB_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
sim.rc.__config__["!SIM.file.local_packages_path"] = IRDB_DIR

PLOTS = False


class TestMosaicMvp:
    def test_initialise_command_object(self):
        cmds = sim.UserCommands(use_instrument="MOSAIC")
        assert isinstance(cmds, sim.UserCommands)
        assert len(cmds.yaml_dicts) > 2

    def test_initialise_optical_train_object(self):
        cmds = sim.UserCommands(use_instrument="MOSAIC")
        mosaic = sim.OpticalTrain(cmds)
        assert isinstance(mosaic, sim.OpticalTrain)


class TestMosiacMvpCanObserveSomething:
    def test_run_observe(self):
        src = st.empty_sky()

        cmds = sim.UserCommands(use_instrument="MOSAIC")
        mosaic = sim.OpticalTrain(cmds)
        mosaic.cmds["!ATMO.temperature"] = 0

        mosaic.observe(src)
        hdul = mosaic.readout()[0]

        im = mosaic.image_planes[0].data
        im2 = hdul[1].data

        if PLOTS:
            plt.figure(figsize=(13, 6))
            plt.subplot(121)
            plt.imshow(im, norm=LogNorm(), origin="lower")
            plt.subplot(122)
            plt.imshow(im2, origin="lower")
            plt.pause(0)
            plt.show()

        # assert im[:, :].sum()

    def test_run_observe_with_star(self):
        src = st.star(0, 0, 25*u.mag)
        wave = np.linspace(1.420, 1.825, 4096) * u.um

        cmds = sim.UserCommands(use_instrument="MOSAIC")
        mosaic = sim.OpticalTrain(cmds)
        mosaic.cmds["!ATMO.temperature"] = 0

        mosaic.observe(src)
        im = mosaic.image_planes[0].data

        mosaic.cmds["!OBS.dit"] = 3600
        hdul = mosaic.readout()[0]

        # in and out fluxes are in units of "ph / s"
        in_flux = (np.trapz(src.spectra[0](wave), wave) *
                   src.fields[0]["weight"] *
                   (mosaic.cmds["!TEL.area"] *
                    1 * u.s)).to(u.ph).value
        out_flux = np.sum(mosaic._last_fovs[0].hdu.data)
        im2 = hdul[1].data

        if not PLOTS:
            plt.figure(figsize=(13, 6))
            plt.subplot(121)
            plt.imshow(im, norm=LogNorm(), origin="lower")
            plt.subplot(122)
            plt.imshow(im2, origin="lower")
            plt.pause(0)
            plt.show()

        # assert in_flux == approx(out_flux)

class TestRadiometryOfMvp:
    def test_same_number_of_photons_go_in_and_out(self):
        pass
