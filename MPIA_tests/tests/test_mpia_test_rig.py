import pytest
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import scopesim as sim
from scopesim.source import source_templates as st

PLOTS = True

PATH_HERE = Path(__file__).parent
PATH_IRDB = PATH_HERE.parent.parent
sim.rc.__config__["!SIM.file.local_packages_path"] = str(PATH_IRDB)


class TestUserCommands:
    def test_config_files_can_be_read(self):
        cmd = sim.UserCommands(use_instrument="MPIA_tests")
        assert len(cmd.yaml_dicts) > 2

class TestOpticalTrain:
    def test_creates_model_of_test_rig(self):
        cmd = sim.UserCommands(use_instrument="MPIA_tests")
        opt = sim.OpticalTrain(cmd)
        assert len(opt.effects) > 2
        assert "MICADO" in opt["filter_wheel"].filters["Ks"].meta["history"][0]

    def test_observe_empty_sky(self):
        src = st.empty_sky()
        opt = sim.OpticalTrain("MPIA_tests")
        opt.observe(src)
