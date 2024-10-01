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

print("Done with all the library installation")



PLOTS = True

# ----------------------------------------------------
# Define VibrationPSF for vibration-affected PSF
# ----------------------------------------------------

class VibrationPSF:
    """
    Gaussian kernel for vibration-affected PSF.
    Produces an elongated PSF along the vibration axis.
    """

    def __init__(self, fwhm=5.0, amplitude=1.5, vibration_axis="x"):
        """
        Initialize the Vibration PSF for telescope vibrations.
        
        Parameters:
        -----------
        fwhm : float
            Full width at half maximum (FWHM) of the PSF in arcseconds.
        amplitude : float
            Amplitude of the vibration effect, controlling elongation of the PSF.
        vibration_axis : str
            Axis along which vibration occurs, either "x" or "y".
        """
        self.fwhm = fwhm  # FWHM in arcseconds
        self.amplitude = amplitude  # Vibration amplitude controlling the elongation
        self.vibration_axis = vibration_axis  # Vibration axis ("x" or "y")

    def get_kernel(self, pixel_scale):
        """
        Calculate the vibration-affected Gaussian kernel.
        
        Parameters:
        -----------
        pixel_scale : float
            The pixel scale in arcseconds per pixel.

        Returns:
        --------
        kernel : np.ndarray
            The vibration-affected PSF kernel.
        """
        # Convert FWHM to standard deviation (sigma) in pixels
        sigma = self.fwhm / 2.35 / pixel_scale
        
        # Adjust sigma based on the vibration axis and amplitude
        if self.vibration_axis == "x":
            sigma_x = sigma * self.amplitude  # Elongated along the x-axis
            sigma_y = sigma  # Normal along the y-axis
        else:
            sigma_x = sigma  # Normal along the x-axis
            sigma_y = sigma * self.amplitude  # Elongated along the y-axis
        
        # Create a 2D Gaussian kernel with vibration effect
        kernel = Gaussian2DKernel(x_stddev=sigma_x, y_stddev=sigma_y, mode="center").array
        kernel /= np.sum(kernel)  # Normalize the kernel to have unit sum
        
        return kernel

    def plot(self, pixel_scale):
        """
        Plot the Vibration-affected PSF using Matplotlib.
        
        Parameters:
        -----------
        pixel_scale : float
            The pixel scale in arcseconds per pixel.
        """
        kernel = self.get_kernel(pixel_scale)

        # Define axis values in arcseconds instead of pixels
        size = kernel.shape[0]  # Assuming the kernel is square
        arcsec_extent = size * pixel_scale / 2  # Half the extent for centered plot
        x = np.linspace(-arcsec_extent, arcsec_extent, size)
        y = np.linspace(-arcsec_extent, arcsec_extent, size)

        plt.figure(figsize=(8, 6))
        plt.imshow(kernel, origin='lower', extent=[x[0], x[-1], y[0], y[-1]], cmap='plasma',norm=LogNorm(vmin=1e-6, vmax=1))  # Adjust vmin and vmax as necessary
        plt.colorbar(label='Intensity')
        plt.title(f"Vibration PSF (FWHM = {self.fwhm} arcsec, Axis = {self.vibration_axis})")
        plt.xlabel("X [arcseconds]")
        plt.ylabel("Y [arcseconds]")
        plt.gca().set_aspect('equal', adjustable='box')  # Equal aspect ratio
        plt.grid(False)  # Optional: disable grid for clarity
        plt.show()


# ----------------------------------------------------
# DREAMS Simulation Setup
# ----------------------------------------------------

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

# ----------------------------------------------------
# Apply the VibrationPSF to DREAMS Simulation Results
# ----------------------------------------------------

# Define the pixel scale for DREAMS
pixel_scale = 2.48  # Arcseconds per pixel for DREAMS

# Instantiate the VibrationPSF class
vibration_psf = VibrationPSF(fwhm=5, amplitude=1.5, vibration_axis="x")  # Elongation along the x-axis

# Plot the vibration-affected PSF
vibration_psf.plot(pixel_scale=pixel_scale)
