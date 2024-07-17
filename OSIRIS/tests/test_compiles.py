from pathlib import Path
import pytest

import numpy as np
import scopesim as sim
from astropy import units as u
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from scopesim.source.source_templates import star_field, star

PATH_HERE = Path(__file__).parent
sim.rc.__config__["!SIM.file.local_packages_path"] = str(PATH_HERE.parent.parent)

PLOTS = False


class TestOsirisImagingCompiles:
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

    @pytest.mark.slow
    def test_run_imaging_simulation(self):
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


class TestOsirisLongSlitCompiles:
    def test_everything_is_read_in_nicely(self):
        cmds = sim.UserCommands(use_instrument="OSIRIS", set_modes=["LSS"])

        assert isinstance(cmds, sim.UserCommands)
        assert len(cmds.yaml_dicts) > 2

    @pytest.mark.slow
    def test_run_lss_simulation(self):
        # n stars, mag_min, mag_max, width=[arcsec]
        src1 = star(x=-3.8, y=-3.8, flux=10*u.mag)
        src3 = star(x=3.8,  y=3.8,  flux=20*u.mag)
        src4 = star(x=-100, y=-3.8, flux=10*u.mag)
        src5 = star(x=100,  y=-3.8, flux=10*u.mag)

        src_comb = src1 + src3 + src4 + src5

        cmds = sim.UserCommands(
            use_instrument="OSIRIS",
            set_modes=["LSS"],
            properties={
                # dit is used in the optical train,
                # while exptime ends up in the headers
                "!OBS.dit": 60,
                "!OBS.exptime": 60,
            })
        cmds["!ATMO.seeing"] = 0.8
        cmds["!OBS.grating_name"] = "R2500V"

        osiris = sim.OpticalTrain(cmds)
        osiris.observe(src_comb)
        hdulist = osiris.readout()[0]

        if PLOTS:
            plt.imshow(hdulist[1].data, norm=LogNorm())
            plt.colorbar()
            plt.show()

        assert hdulist[1].data.max() > 1e3


class TestOsirisMaatCompiles:
    def test_everything_is_read_in_nicely(self):
        cmds = sim.UserCommands(use_instrument="OSIRIS", set_modes=["MAAT"])

        assert isinstance(cmds, sim.UserCommands)
        assert len(cmds.yaml_dicts) > 2

    @pytest.mark.slow
    def test_run_maat_simulation(self):
        # n stars, mag_min, mag_max, width=[arcsec]
        src = star_field(5**2, 10, 10, 8, use_grid=True)

        cmds = sim.UserCommands(
            use_instrument="OSIRIS",
            set_modes=["MAAT"],
            properties={
                "!OBS.dit": 60,
                "!OBS.exptime": 60,
            })
        cmds["!ATMO.seeing"] = 0.8
        # cmds["!OBS.grating_name"] = "R2500V"

        osiris = sim.OpticalTrain(cmds)
        osiris.observe(src)
        hdulist = osiris.readout()[0]

        if PLOTS:
            plt.imshow(hdulist[1].data, norm=LogNorm())
            plt.colorbar()
            plt.show()

        assert hdulist[1].data.max() > 1e3
