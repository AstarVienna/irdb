"""
Tests the SPEC mode, that it compiles and runs.

Ideally this will also contain a flux consistency test or two

Comments
--------
- 2022-03-18 (KL)

"""

# integration test using everything and the MICADO package
import pytest
from pytest import approx

import numpy as np

import scopesim as sim
from scopesim import rc
from scopesim.source import source_templates as st

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

rc.__config__["!SIM.file.local_packages_path"] = "../../"
PLOTS = False


class TestInit:
    @pytest.mark.parametrize("modes", [["SCAO", "SPEC_3000x20"],
                                       ["SCAO", "SPEC_3000x50"],
                                       ["SCAO", "SPEC_15000x50"]])
    def test_loads_optical_train(self, modes):
        cmds = sim.UserCommands(use_instrument="MICADO", set_modes=modes)
        micado = sim.OpticalTrain(cmds)
        opt_els = np.unique(micado.effects["element"])

        assert isinstance(micado, sim.OpticalTrain)
        assert len(opt_els) == 6

    def test_runs_spec_hk_3000x30(self):
        src = st.empty_sky()

        cmds = sim.UserCommands(use_instrument="MICADO",
                                set_modes=["SCAO", "SPEC_3000x20"])
        # cmds.cmds["!OBS.trace_file"] = "TRACES_MICADO_220223.fits"    # New, only 4 (HK) traces
        cmds.cmds["!OBS.trace_file"] = "TRACE_MICADO.fits"      # Old, missing x=0
        micado = sim.OpticalTrain(cmds)
        # micado.cmds["!DET.width"] = 4096*3
        # micado.cmds["!DET.height"] = 4096*3
        micado["detector_window"].include = False
        micado["full_detector_array"].include = True

        micado.observe(src)
        micado.image_planes[0].hdu.writeto("TEST_implane.fits")
        micado.readout("TEST_readout.fits")

        # plt.subplot(121)
        # plt.imshow(micado.image_planes[0].data, norm=LogNorm(), origin="lower")
        #
        # plt.subplot(122)
        # plt.imshow(hdul[1].data, norm=LogNorm(), origin="lower")
        #
        # plt.show()
