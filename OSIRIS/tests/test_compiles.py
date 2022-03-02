import os

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

from scopesim.source.source_templates import star_field
import scopesim as sim

sim.rc.__config__["!SIM.file.local_packages_path"] = os.path.abspath("../../")

PLOTS = True


class TestOsirisCompiles:
    def test_everything_is_read_in_nicely(self):
        cmds = sim.UserCommands(use_instrument="OSIRIS")

        assert isinstance(cmds, sim.UserCommands)
        assert len(cmds.yaml_dicts) > 2

    def test_can_make_optical_train(self):
        cmds = sim.UserCommands(use_instrument="OSIRIS")
        osiris = sim.OpticalTrain(cmds)

        assert isinstance(osiris, sim.OpticalTrain)

    def test_run_simulation(self):
        # n stars, mag_min, mag_max, width=[arcsec]
        src = star_field(n=400, mmin=10, mmax=20, width=60)

        cmds = sim.UserCommands(use_instrument="OSIRIS")
        osiris = sim.OpticalTrain(cmds)
        osiris.observe(src)
        hdulist = osiris.readout()[0]

        if PLOTS:
            plt.imshow(hdulist[1].data, norm=LogNorm())
            plt.imshow()
