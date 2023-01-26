import pytest
from os import path as pth
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import scopesim as sim

IRDB_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
sim.rc.__config__["!SIM.file.local_packages_path"] = IRDB_DIR

PLOTS = True


class TestMosaicMvp:
    def test_initialise_command_object(self):
        cmds = sim.UserCommands(use_instrument="MOSAIC")
        assert isinstance(cmds, sim.UserCommands)
        assert len(cmds.yaml_dicts) > 2

    def test_initialise_optical_train_object(self):
        cmds = sim.UserCommands(use_instrument="MOSAIC")
        mosaic = sim.OpticalTrain(cmds)
        assert isinstance(mosaic, sim.OpticalTrain)


class TestMosiacMvpCanObserveSomething:
    from scopesim.source import source_templates as st
    src = st.empty_sky()

    cmds = sim.UserCommands(use_instrument="MOSAIC")
    mosaic = sim.OpticalTrain(cmds)

    mosaic.observe(src)

    if PLOTS:
        plt.imshow(mosaic.image_planes[0].data.T, norm=LogNorm())
        plt.pause(0)
        plt.show()





