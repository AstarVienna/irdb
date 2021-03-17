'''Basic unit tests for irdb/METIS'''
# pylint: disable=R0201

import os
#import pytest
import numpy as np
#from astropy.io.fits import HDUList
#from astropy import units as u
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

import scopesim
from scopesim.source.source_templates import star_field
#import scopesim_templates as sim_tp

PLOTS = True
PKGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
scopesim.rc.__config__["!SIM.file.local_packages_path"] = PKGS_DIR


class TestLoads:
    '''Test that irdb/METIS is loaded and an OpticalTrain is produced'''
    def test_scopesim_loads_package(self):
        '''Load the configuration from default.yaml. Modes other than
        the default are not tested.'''
        metis = scopesim.OpticalTrain("METIS")
        assert isinstance(metis, scopesim.OpticalTrain)


class TestObserves:
    '''Test basic observations for the main instrument modes'''
    def test_something_comes_out_img_lm(self):
        '''Basic test for LM imaging'''
        src = star_field(100, 15, 25, width=10, use_grid=True)

        cmds = scopesim.UserCommands(use_instrument="METIS",
                                     set_modes=['img_lm'])
        metis = scopesim.OpticalTrain(cmds)
        metis['scope_vibration'].include = False
        metis['detector_linearity'].include = False

        metis.observe(src)
        hdus = metis.readout()

        if PLOTS:
            img = hdus[0][1].data
            plt.imshow(img,
                       norm=LogNorm(vmin=0.7*np.median(img),
                                    vmax=1.3*np.median(img)))
            plt.title("LM Imaging Test")
            plt.colorbar()

            plt.show()


    def test_something_comes_out_img_n(self):
        '''Basic test for N imaging'''
        src = star_field(100, 5, 15, width=10, use_grid=True)

        cmds = scopesim.UserCommands(use_instrument="METIS",
                                     set_modes=["img_n"])

        metis = scopesim.OpticalTrain(cmds)
        #metis.cmds.set_modes("img_n")
        metis['scope_vibration'].include = False
        metis['detector_linearity'].include = False

        metis.observe(src)
        hdus = metis.readout()

        if PLOTS:
            img = hdus[0][1].data
            plt.imshow(img, norm=LogNorm(vmin=0.7*np.median(img),
                                         vmax=1.3*np.median(img)))
            plt.title("N Imaging Test")
            plt.colorbar()

            plt.show()
