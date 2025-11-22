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
from scopesim_templates.stellar import cluster

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
src = cluster(mass=1000,  distance=50000, core_radius=500, seed=9002)

dreams.observe(src)
print("yessss anjali")
hdus = dreams.readout()
dreams.readout(filename="Lc.fits")
#plt.subplot(121)
#wave = np.arange(3000, 11000)
#plt.plot(wave, dreams.optics_manager.system_transmission(wave))
plt.subplot(122)
im = hdus[0][1].data
plt.imshow(im, norm=LogNorm())
plt.colorbar()
plt.title("Observed Star Field")
plt.xlabel("X Pixels")
plt.ylabel("Y Pixels")
plt.grid()
plt.show()
