import os
import pytest
import numpy as np
from astropy.io.fits import HDUList
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm


import scopesim
from scopesim.source.source_templates import star_field
import scopesim_templates as sim_tp


PLOTS = False
PKGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
scopesim.rc.__config__["!SIM.file.local_packages_path"] = PKGS_DIR


class TestLoads:
    def test_scopesim_loads_package(self):
        lfoa = scopesim.OpticalTrain("ViennaLT")
        assert isinstance(lfoa, scopesim.OpticalTrain)


@pytest.mark.slow
class TestObserves:
    def test_something_comes_out(self):
        src = star_field(100, 0, 10, width=360, use_grid=True)

        cmds = scopesim.UserCommands(use_instrument="ViennaLT")
        cmds["!OBS.dit"] = 300
        cmds["!OBS.ndit"] = 1
        cmds["!OBS.filter_name"] = "sloan_z"

        lfoa = scopesim.OpticalTrain(cmds)
        lfoa.observe(src)
        hdus = lfoa.readout()

        if PLOTS:
            plt.subplot(121)
            wave = np.arange(3000, 11000)
            plt.plot(wave, lfoa.optics_manager.system_transmission(wave))

            plt.subplot(122)
            im = hdus[0][1].data
            plt.imshow(im, norm=LogNorm())
            plt.colorbar()

            plt.show()

    def test_observes_from_scopesim_templates(self):
        src = sim_tp.stellar.cluster(mass=10000, distance=2000, core_radius=1)

        lfoa = scopesim.OpticalTrain("ViennaLT")
        lfoa.observe(src)

        lfoa.cmds["!OBS.dit"] = 100
        hdus = lfoa.readout()

        assert isinstance(hdus[0], HDUList)

        if PLOTS:
            im = hdus[0][1].data
            plt.imshow(im, norm=LogNorm(), cmap="hot")
            plt.colorbar()
            plt.show()

    def test_saves_readout_to_disc(self):
        src = sim_tp.stellar.cluster(mass=10000, distance=2000, core_radius=1)
        lfoa = scopesim.OpticalTrain("ViennaLT")
        lfoa.observe(src)
        lfoa.readout(filename="TEST.fits")

        assert os.path.exists("TEST.fits")


class TestGetOptions:
    def test_print_obs_options(self):
        cmds = scopesim.UserCommands(use_instrument="ViennaLT")
        lfoa = scopesim.OpticalTrain("LFOA")
        print(cmds)
