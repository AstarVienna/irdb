import os
import pytest
import numpy as np
from astropy.io.fits import HDUList
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import scopesim

from scopesim import rc
from scopesim.source.source_templates import star_field
import scopesim_templates as sim_tp

PLOTS = True

if rc.__config__["!SIM.tests.run_integration_tests"] is False:
    pytestmark = pytest.mark.skip("Ignoring DREAMS integration tests")


class TestLoads:
    def test_scopesim_loads_package(self):
        dreams = scopesim.OpticalTrain("DREAMS")
        assert isinstance(dreams, scopesim.OpticalTrain)  # Corrected syntax
        print("scopesim package loaded successfully.")


class TestObserves:
    def test_something_comes_out(self):
        print("Starting observation test...")

        # Setting the width to 10000 arcsec makes the field fill the image.
        # A with of 700 works as well, but covers only a fraction of the
        # middle two detectors.
        src = star_field(10000, 10, 20, width=10000)

        cmds = scopesim.UserCommands(use_instrument="DREAMS")
        cmds["!OBS.dit"] = 8
        cmds["!DET.bin_size"] = 1
        cmds["!OBS.sky.bg_mag"] = 14.9
        cmds["!OBS.sky.filter_name"] = "J"
        cmds["SIM.sub_pixel.flag"] = True

        dreams = scopesim.OpticalTrain(cmds)
        dreams["detector_linearity"].include = False

        dreams.observe(src)

        hdus = dreams.readout("dreams.fits")

        print(f"Observation completed. HDUList type: {type(hdus[0])}")

        if PLOTS:
            plt.subplot(121)
            wave = np.arange(3000, 11000)
            plt.plot(wave, dreams.optics_manager.system_transmission(wave))

            plt.subplot(122)
            im = hdus[0][1].data
            plt.imshow(im, norm=LogNorm())
            plt.colorbar()
            plt.title("Observed Star Field")
            plt.xlabel("X Pixels")
            plt.ylabel("Y Pixels")
            plt.grid()
            plt.show()

            detector_order = [2, 1, 4, 3, 6, 5]
            plt.figure(figsize=(20, 20))
            for plot_number, hdu_number in enumerate(detector_order, 1):
                plt.subplot(3, 2, plot_number)
                data = hdus[0][hdu_number].data
                med = np.median(data)
                std = np.std(data)
                vmin = med
                vmax = med + 5 * std
                plt.imshow(data, origin="lower", norm=LogNorm(vmin=vmin, vmax=vmax))
                plt.colorbar()
            plt.show()

    @pytest.mark.slow
    def test_observes_from_scopesim_templates(self):
        print("Starting scopesim templates observation test...")
        src = sim_tp.stellar.cluster(mass=10000, distance=2000, core_radius=1)

        dreams = scopesim.OpticalTrain("DREAMS")
        dreams.observe(src)

        dreams.cmds["!OBS.dit"] = 10
        hdus = dreams.readout()

        assert isinstance(hdus[0], HDUList)
        print("Observation from scopesim templates completed.")

        if PLOTS:
            im = hdus[0][1].data
            plt.imshow(im, norm=LogNorm(), cmap="hot")
            plt.colorbar()
            plt.show()

    @pytest.mark.slow
    def test_saves_readout_to_disc(self):
        print("Starting test to save readout to disk...")
        src = sim_tp.stellar.cluster(mass=10000, distance=2000, core_radius=1)
        dreams = scopesim.OpticalTrain("DREAMS")
        dreams.observe(src)
        dreams.readout(filename="GNANU.fits")

        assert os.path.exists("GNANU.fits")
        print("Readout saved to GNANU.fits.")


def run_test_and_plot():
    test_observes = TestObserves()
    test_observes.test_something_comes_out()


# Run the test and plot as soon as the module is imported
if __name__ == '__main__':
    run_test_and_plot()
