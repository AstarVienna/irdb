#cluster in the LMC
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
src = sim_tp.stellar.clusters.cluster(mass=10000,  distance=1800, core_radius=500, seed=9002)

dreams.observe(src)
print("yessss anjali")
hdus = dreams.readout()
#dreams.readout(filename="Han.fits")
plt.subplot(121)
wave = np.arange(3000, 11000)
plt.plot(wave, dreams.optics_manager.system_transmission(wave))
plt.subplot(122)
im = hdus[0][1].data
# detector_order = [2, 1, 4, 3, 6, 5]
detector_order = [1, 2, 3, 4, 5, 6]
plt.figure(figsize=(20, 20))
for plot_number, hdu_number in enumerate(detector_order, 1):
    plt.subplot(3, 2, plot_number)
    plt.imshow(hdus[0][hdu_number].data, norm=LogNorm(), cmap="hot")
    plt.colorbar()
    
plt.show()
