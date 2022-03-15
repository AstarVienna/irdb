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
from scopesim.source import source_templates as st

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

if rc.__config__["!SIM.tests.run_integration_tests"] is False:
    pytestmark = pytest.mark.skip("Ignoring MICADO integration tests")

TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH


class TestInit:
    def test_loads_spec_mode(self):
        cmds = sim.UserCommands(use_instrument="MICADO",
                                set_modes=["SCAO", "SPEC_3000x50"])
        micado = sim.OpticalTrain(cmds)

        assert isinstance(micado, sim.OpticalTrain)

    def other(self):
        src = st.empty_sky()
