import os
import pytest
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import scopesim
from scopesim import Source, rc
from scopesim_templates.extragalactic import galaxy
from scopesim.source.source_templates import star_field
from scopesim.optics.fov_manager import FOVManager
from astropy.io import fits

PLOTS = True

# Check if integration tests should be skipped
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

# Initialize UserCommands for DREAMS
cmds = scopesim.UserCommands(use_instrument="DREAMS")
cmds["!OBS.dit"] = 10
cmds["!DET.bin_size"] = 1
cmds["!OBS.sky.bg_mag"] = 14.9
cmds["!OBS.sky.filter_name"] = "J"
cmds["SIM.sub_pixel.flag"] = True

# Set up the optical train
dreams = scopesim.OpticalTrain(cmds)
dreams["detector_linearity"].include = False

# Configure the field of view
dreams.fov_manager = FOVManager(dreams.optics_manager.fov_setup_effects, cmds=dreams.cmds, preload_fovs=False)
dreams.fov_manager.volumes_list[0]["x_min"] = -18000  # arcsec
dreams.fov_manager.volumes_list[0]["x_max"] = 18000
dreams.fov_manager.volumes_list[0]["y_min"] = -18000
dreams.fov_manager.volumes_list[0]["y_max"] = 18000
dreams.fov_manager._fovs_list = list(dreams.fov_manager.generate_fovs_list())

print("scopesim package loaded successfully.")

# Create a galaxy source
src = galaxy("kc96/s0", z=0.1, amplitude=17, filter_curve="J", pixel_scale=0.05, r_eff=2.5, n=4, ellip=0.5, theta=45, extend=3)

# Observe the source
dreams.observe(src, update=False)

# Readout and plot
hdus = dreams.readout()

plt.subplot(121)
wave = np.arange(3000, 11000)
plt.plot(wave, dreams.optics_manager.surfaces_table.throughput(wave))

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


