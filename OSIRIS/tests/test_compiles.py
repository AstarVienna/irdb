import os
import numpy as np

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

from astropy import units as u

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

    def test_system_throughput_is_not_zero(self):
        cmds = sim.UserCommands(use_instrument="OSIRIS")
        osiris = sim.OpticalTrain(cmds)
        wave = np.arange(0.3, 1.0, 0.001) * u.um
        trans = osiris.optics_manager.system_transmission(wave)

        if PLOTS:
            plt.plot(wave, trans)
            plt.show()

        assert trans.sum() > 0

    def test_run_simulation(self):
        # n stars, mag_min, mag_max, width=[arcsec]
        src = star_field(n=1000, mmin=10, mmax=20, width=450, use_grid=False)

        cmds = sim.UserCommands(use_instrument="OSIRIS")
        osiris = sim.OpticalTrain(cmds)
        osiris.observe(src)
        hdulist = osiris.readout()[0]

        if PLOTS:
            plt.imshow(hdulist[1].data, norm=LogNorm())
            plt.colorbar()
            plt.show()
