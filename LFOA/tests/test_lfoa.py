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
        lfoa = scopesim.OpticalTrain("LFOA")
        assert isinstance(lfoa, scopesim.OpticalTrain)


class TestObserves:
    def test_something_comes_out(self):
        src = star_field(100, 15, 25, width=360, use_grid=True)

        cmds = scopesim.UserCommands(use_instrument="LFOA")
        cmds["!OBS.dit"] = 30
        cmds["!OBS.ndit"] = 1
        cmds["!OBS.filter_name"] = "sloan_z"

        lfoa = scopesim.OpticalTrain(cmds)
        lfoa.observe(src)
        hdus = lfoa.readout()

        if PLOTS:
            plt.subplot(121)
            wave = np.arange(3000, 11000)
            plt.plot(wave, lfoa.optics_manager.system_tranmission(wave))

            plt.subplot(122)
            im = hdus[0][1].data
            plt.imshow(im, norm=LogNorm())
            plt.colorbar()

            plt.show()

    @pytest.mark.slow
    def test_observes_from_scopesim_templates(self):
        src = sim_tp.stellar.cluster(mass=10000, distance=2000, core_radius=1)

        lfoa = scopesim.OpticalTrain("LFOA")
        lfoa.observe(src)

        lfoa.cmds["!OBS.dit"] = 100
        hdus = lfoa.readout()

        assert isinstance(hdus[0], HDUList)

        if PLOTS:
            im = hdus[0][1].data
            plt.imshow(im, norm=LogNorm(), cmap="hot")
            plt.colorbar()
            plt.show()

    @pytest.mark.slow
    def test_saves_readout_to_disc(self):
        src = sim_tp.stellar.cluster(mass=10000, distance=2000, core_radius=1)
        lfoa = scopesim.OpticalTrain("LFOA")
        lfoa.observe(src)
        lfoa.readout(filename="TEST.fits")

        assert os.path.exists("TEST.fits")
