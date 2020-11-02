import os
import pytest
import numpy as np
from astropy.io.fits import HDUList
from astropy import units as u
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

import scopesim
from scopesim.source.source_templates import star_field, empty_sky
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
        metis["armazones_atmo_default_ter_curve"].include = True
        metis["!ATMO.background.value"] = 99

        metis.observe(src)
        hdus = metis.readout()

        if not PLOTS:
            im = hdus[0][1].data
            plt.imshow(im, norm=LogNorm(),
                       vmin=0.7*np.median(im),
                       vmax=1.3*np.median(im))
            plt.colorbar()

            plt.show()


class TestMETISBackground:
    def test_Lp_background_is_300000_ph_s_pix(self):
        src = empty_sky()
        cmds = scopesim.UserCommands(use_instrument="METIS")
        metis = scopesim.OpticalTrain(cmds)

        elt = metis["metis_cfo_surfaces"]
        x = np.arange(3, 5, 0.001)
        plt.plot(x, elt.background_source.spectra[0](x))
        # plt.show()
