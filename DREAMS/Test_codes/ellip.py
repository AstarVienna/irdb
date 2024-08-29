#Elliptical Galaxy
import os
import pytest
import numpy as np
from astropy.io.fits import HDUList
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import scopesim
import synphot
from scopesim_templates.extragalactic.galaxies import elliptical
from astropy.io import fits


from scopesim import rc
from scopesim.source.source_templates import star_field
import scopesim_templates as sim_tp
from scopesim.optics.fov_manager import FOVManager

PLOTS = True

if rc.__config__["!SIM.tests.run_integration_tests"] is False:
    pytestmark = pytest.mark.skip("Ignoring DREAMS integration tests")

# Set TOP_PATH to the directory containing the DREAMS package
TOP_PATH = "/Users/anjali/Desktop"
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH

# Adjust the PKGS dictionary to reflect the correct path
PKGS = {"DREAMS": os.path.join(TOP_PATH, "DREAMS")}

# Verify the path to the DREAMS package
if not os.path.exists(PKGS["DREAMS"]):
    raise FileNotFoundError(f"DREAMS package not found at {PKGS['DREAMS']}")
else:
    print("DREAMS package found at:", PKGS["DREAMS"])

cmds = scopesim.UserCommands(use_instrument="DREAMS")
cmds["!OBS.dit"] = 1000
cmds["!OBS.ndit"] = 1000
cmds["!DET.bin_size"] = 1
cmds["!OBS.sky.bg_mag"] = 14.9
cmds["!OBS.sky.filter_name"] = "J"
cmds["SIM.sub_pixel.flag"] = True
dreams = scopesim.OpticalTrain(cmds)
dreams["detector_linearity"].include = False
dreams.fov_manager = FOVManager(dreams.optics_manager.fov_setup_effects, cmds=dreams.cmds, preload_fovs=False)
# Then make the initial field of view 10 times larges than normal.
dreams.fov_manager.volumes_list[0]["x_min"] = -18000  # arcsec
dreams.fov_manager.volumes_list[0]["x_max"] = 18000
dreams.fov_manager.volumes_list[0]["y_min"] = -18000
dreams.fov_manager.volumes_list[0]["y_max"] = 18000
# Finally, shrink the field of view to the detector size.
dreams.fov_manager._fovs_list = list(dreams.fov_manager.generate_fovs_list())

print("scopesim package loaded successfully.")
src = elliptical(half_light_radius=11500, pixel_scale=2.48, filter_name="J", amplitude=17, normalization="total", n=4, ellipticity=0.5, angle=30)
dreams.observe(src, update=False)
hdus = dreams.readout()
dreams.readout(filename="ellip.fits")
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
