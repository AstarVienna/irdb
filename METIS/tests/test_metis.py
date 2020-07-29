import os
import pytest
import numpy as np
from astropy.io.fits import HDUList
from astropy import units as u
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
        metis = scopesim.OpticalTrain("METIS")
        assert isinstance(metis, scopesim.OpticalTrain)


class TestObserves:
    def test_something_comes_out(self):
        src = star_field(100, 15, 25, width=10, use_grid=True)

        cmds = scopesim.UserCommands(use_instrument="METIS")

        metis = scopesim.OpticalTrain(cmds)
        metis['scope_vibration'].include = False
        metis['detector_linearity'].include = False

        metis.observe(src)
        hdus = metis.readout()

        if not PLOTS:
            plt.subplot(121)
            wave = np.arange(3, 5, 0.001) * u.um
            thru = metis.optics_manager.surfaces_table.throughput(wave)
            plt.plot(wave, thru)

            plt.subplot(122)
            im = hdus[0][1].data
            plt.imshow(im, norm=LogNorm())
            plt.colorbar()

            plt.show()
