import pytest
from os import path as pth
import scopesim as sim

IRDB_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
sim.rc.__config__["!SIM.file.local_packages_path"] = IRDB_DIR

class TestMosaicMvp:
    def test_initialise_command_object(self):
        cmds = sim.UserCommands(use_instrument="MOSAIC")
        assert isinstance(cmds, sim.UserCommands)
        assert len(cmds.yaml_dicts) > 2

    def test_initialise_optical_train_object(self):
        cmds = sim.UserCommands(use_instrument="MOSAIC")
        mosaic = sim.OpticalTrain(cmds)
        assert isinstance(mosaic, sim.OpticalTrain)
