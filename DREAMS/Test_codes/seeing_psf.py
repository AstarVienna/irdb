import os
import pytest
import numpy as np
from astropy.io.fits import HDUList
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import scopesim
from astropy.convolution import Gaussian2DKernel
from scopesim import rc
from scopesim_templates.stellar import star_field, star_grid
import scopesim_templates as sim_tp
from scopesim.optics.fov_manager import FOVManager
from astropy import units as u
from scopesim.utils import quantify

PLOTS = True

if rc.__config__["!SIM.tests.run_integration_tests"] is False:
    pytestmark = pytest.mark.skip("Ignoring DREAMS integration tests")

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

dreams = scopesim.OpticalTrain(cmds)
dreams["detector_linearity"].include = False

# Perform observation
dreams.observe(src)
hdus = dreams.readout("uncrowded.fits")
print(f"Observation completed. HDUList type: {type(hdus[0])}")

# ----------------------------------------------------
# Define and Plot the SeeingPSF in Arcseconds
# ----------------------------------------------------
class SeeingPSF:
    """
    Gaussian kernel for seeing-limited PSF.
    """

    def __init__(self, fwhm=1.5):
        self.fwhm = fwhm  # FWHM in arcseconds

    def get_kernel(self, pixel_scale):
        """
        Calculate Gaussian kernel for the given pixel scale and FWHM.
        
        Parameters:
        -----------
        pixel_scale : float
            The pixel scale in arcseconds/pixel.

        Returns:
        --------
        kernel : np.ndarray
            The Gaussian PSF kernel.
        """
        sigma = self.fwhm / 2.35 / pixel_scale
        kernel = Gaussian2DKernel(sigma, mode="center").array
        kernel /= np.sum(kernel)  # Normalize the kernel
        return kernel

    def plot(self, pixel_scale):
        """
        Plot the Seeing PSF in arcseconds using Matplotlib.
        """
        kernel = self.get_kernel(pixel_scale)

        # Define axis values in arcseconds instead of pixels
        size = kernel.shape[0]  # Assuming the kernel is square
        arcsec_extent = size * pixel_scale / 2  # Half the extent for centered plot
        x = np.linspace(-arcsec_extent, arcsec_extent, size)
        y = np.linspace(-arcsec_extent, arcsec_extent, size)

        plt.figure(figsize=(6, 6))
        plt.imshow(kernel, origin='lower', extent=[x[0], x[-1], y[0], y[-1]], cmap='plasma', norm=LogNorm())
        #plt.contour(x, y, kernel, colors='white', linewidths=0.5)  # Add contours

        plt.colorbar(label='Intensity')
        plt.title(f"Seeing PSF (FWHM = {self.fwhm} arcsec")
        plt.xlabel("X [arcseconds]")
        plt.ylabel("Y [arcseconds]")
        plt.show()

# Set the pixel scale and FWHM
pixel_scale = 2.48  # Pixel scale of 2.48 arcseconds per pixel
seeing_psf = SeeingPSF(fwhm=5)  # Set FWHM to 5 arcseconds

# Plot the SeeingPSF with arcseconds on the axes
seeing_psf.plot(pixel_scale=pixel_scale)
