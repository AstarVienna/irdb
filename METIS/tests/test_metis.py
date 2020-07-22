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
        lfoa = scopesim.OpticalTrain("METIS")
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