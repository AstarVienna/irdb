import os
import warnings
import numpy as np
from astropy import units as u
from astropy.io.fits import HDUList
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import scopesim
from astropy.convolution import Gaussian2DKernel
from scopesim.utils import quantify
from scopesim import rc
from scopesim_templates.stellar import star_field, star_grid
from scopesim.optics.fov_manager import FOVManager

PLOTS = True
class GaussianDiffractionPSF:
    def __init__(self, diameter=0.1, **kwargs):  # Default diameter is 0.1 m
        self.meta = {"diameter": diameter, "z_order": [242, 642]}
        self.required_keys = {"pixel_scale"}
        self.valid_waverange = [0.1 * u.um, 0.2 * u.um]  # Default wavelength range

    def update(self, **kwargs):
        if "diameter" in kwargs:
            self.meta["diameter"] = kwargs["diameter"]

    def get_kernel(self, pixel_scale):
        wave_min = self.valid_waverange[0].value  # Using default min wave
        wave_max = self.valid_waverange[1].value  # Using default max wave
        wave = 0.5 * (wave_max + wave_min)  # Average wave
        wave = quantify(wave, u.um)
        
        diameter = quantify(self.meta["diameter"], u.m).to(u.um)
        fwhm = 1.22 * (wave / diameter) * u.rad.to(u.arcsec) / pixel_scale

        sigma = fwhm.value / 2.35
        kernel = Gaussian2DKernel(sigma, mode="center").array
        kernel /= np.sum(kernel)

        return kernel

    def plot(self, pixel_scale):
        kernel = self.get_kernel(pixel_scale)

        size = kernel.shape[0]
        arcsec_extent = size * pixel_scale / 2
        x = np.linspace(-arcsec_extent, arcsec_extent, size)
        y = np.linspace(-arcsec_extent, arcsec_extent, size)

        plt.figure(figsize=(8, 6))
        plt.imshow(kernel, origin='lower', extent=[x[0], x[-1], y[0], y[-1]], cmap='plasma', norm=LogNorm(vmin=1e-6, vmax=1))
        plt.colorbar(label='Intensity')
        plt.title(f"Gaussian Diffraction PSF (Diameter = {self.meta['diameter']} m)")
        plt.xlabel("X [arcseconds]")
        plt.ylabel("Y [arcseconds]")
        plt.gca().set_aspect('equal', adjustable='box')
        plt.grid(False)
        plt.show()
if rc.__config__["!SIM.tests.run_integration_tests"] is False:
    pytestmark = pytest.mark.skip("Ignoring DREAMS integration tests")

# Set TOP_PATH to the directory containing the DREAMS package
TOP_PATH = "/Users/anjali/github"
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH

# Adjust the PKGS dictionary to reflect the correct path
PKGS = {"DREAMS": os.path.join(TOP_PATH, "DREAMS")}

# Verify the path to the DREAMS package
if not os.path.exists(PKGS["DREAMS"]):
    raise FileNotFoundError(f"DREAMS package not found at {PKGS['DREAMS']}")
else:
    print("DREAMS package found at:", PKGS["DREAMS"])

# Initialize DREAMS optical train
dreams = scopesim.OpticalTrain("DREAMS")
assert isinstance(dreams, scopesim.OpticalTrain)
print("scopesim package loaded successfully.")

# Create a star field as the source
src = star_field(500, 10, 20, width=100)

# Set up user commands for the DREAMS simulation
cmds = scopesim.UserCommands(use_instrument="DREAMS")
cmds["!OBS.dit"] = 8
cmds["!OBS.ndit"] = 1
cmds["!DET.bin_size"] = 1
cmds["!OBS.sky.bg_mag"] = 14.9  # J-band magnitude
cmds["!OBS.sky.filter_name"] = "J"
cmds["SIM.sub_pixel.flag"] = True

# Reinitialize the optical train with the user commands
dreams = scopesim.OpticalTrain(cmds)
dreams["detector_linearity"].include = False

# Set up the Field of View (FOV) for the simulation
dreams.fov_manager = FOVManager(dreams.optics_manager.fov_setup_effects, cmds=dreams.cmds, preload_fovs=False)
dreams.fov_manager.volumes_list[0]["x_min"] = -18000
dreams.fov_manager.volumes_list[0]["x_max"] = 18000
dreams.fov_manager.volumes_list[0]["y_min"] = -18000
dreams.fov_manager.volumes_list[0]["y_max"] = 18000
dreams.fov_manager._fovs_list = list(dreams.fov_manager.generate_fovs_list())

# Perform observation
dreams.observe(src, update=False)
hdus = dreams.readout("vibration_analysis.fits")
print(f"Observation completed. HDUList type: {type(hdus[0])}")


# Define the pixel scale for DREAMS
pixel_scale = 2.48  # Arcseconds per pixel for DREAMS

# Instantiate the VibrationPSF class
diffraction_psf = GaussianDiffractionPSF(diameter=0.5)

# Get the PSF kernel for a specific pixel scale
pixel_scale = 2.48  # in arcseconds
kernel = diffraction_psf.get_kernel(pixel_scale)

# Plot the PSF
diffraction_psf.plot(pixel_scale)
