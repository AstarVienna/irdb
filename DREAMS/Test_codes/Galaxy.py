# Extragalatic
import os
import pytest
import numpy as np
from astropy.io.fits import HDUList
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import scopesim
import synphot
from scopesim import Source
from astropy.io import fits
from scopesim_templates.extragalactic import galaxy
from scopesim import rc
from scopesim.source.source_templates import star_field
import scopesim_templates as sim_tp
from scopesim.optics.fov_manager import FOVManager

PLOTS = True

if rc.__config__["!SIM.tests.run_integration_tests"] is False:
    pytestmark = pytest.mark.skip("Ignoring DREAMS integration tests")

cmds = scopesim.UserCommands(use_instrument="DREAMS")
cmds["!OBS.dit"] = 1000
cmds["!OBS.ndit"] = 1000
cmds["!DET.bin_size"] = 1
cmds["!OBS.sky.bg_mag"] = 14.9
cmds["!OBS.sky.filter_name"] = "J"
cmds["SIM.sub_pixel.flag"] = True
dreams = scopesim.OpticalTrain(cmds)
dreams["detector_linearity"].include = False

print("scopesim package loaded successfully.")
from scopesim_templates.extragalactic import galaxy
src = galaxy("kc96/s0", z=1.5, amplitude=17, filter_curve="J", pixel_scale=0.01, r_eff=2.5, n=4, ellip=0.5, theta=45, extend=3)

dreams.observe(src)
print("yessss anjali")
hdus = dreams.readout()
dreams.readout(filename="gal.fits")
# Observe the source
dreams.observe(src)

# Readout and plot
hdus = dreams.readout()

plt.subplot(122)
im = hdus[0][1].data
plt.imshow(im, norm=LogNorm())
plt.colorbar()
plt.title("Observed Galaxy Field")
plt.xlabel("X Pixels")
plt.ylabel("Y Pixels")

detector_order = [2, 1, 4, 3, 6, 5]
plt.figure(figsize=(20, 20))
for plot_number, hdu_number in enumerate(detector_order, 1):
    plt.subplot(3, 2, plot_number)
    plt.imshow(np.log10(src.fields[0].data), origin="lower")
    plt.colorbar()
    plt.title(f"HDU {hdu_number}")

plt.show()




