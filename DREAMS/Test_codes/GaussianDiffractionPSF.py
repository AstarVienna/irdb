import os
import numpy as np
from astropy import units as u
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from astropy.convolution import Gaussian2DKernel
from scopesim.utils import quantify
from scopesim import rc
from scopesim_templates.stellar import star_field
from scopesim.optics.fov_manager import FOVManager

# Set plotting flag
PLOTS = True

# GaussianDiffractionPSF Class
class GaussianDiffractionPSF:
    def __init__(self, diameter=0.1, **kwargs):  # Default diameter is 0.1 m
        self.meta = {"diameter": diameter, "z_order": [242, 642]}
        self.required_keys = {"pixel_scale"}
        self.valid_waverange = [11610.0 * u.angstrom.to(u.micron),  # Min wavelength in microns
                                13330.0 * u.angstrom.to(u.micron)]  # Max wavelength in microns

    def update(self, **kwargs):
        if "diameter" in kwargs:
            self.meta["diameter"] = kwargs["diameter"]

    def get_kernel(self, pixel_scale):
        wave_min = 11610.0 * u.angstrom.to(u.micron)  # Using J band min wave
        wave_max =13330.0 * u.angstrom.to(u.micron)  # Using J band max wave
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
        plt.title(f"Gaussian Diffraction PSF (Diameter = {self.meta['diameter']} m, J Band Wavelength)")
        plt.xlabel("X [arcseconds]")
        plt.ylabel("Y [arcseconds]")
        plt.gca().set_aspect('equal', adjustable='box')
        plt.grid(False)
        plt.show()

# Define the pixel scale for DREAMS
pixel_scale = 2.48  # Arcseconds per pixel for DREAMS

# Instantiate the GaussianDiffractionPSF class
gaussian_psf = GaussianDiffractionPSF(diameter=0.5)

# Plot the Gaussian Diffraction PSF
gaussian_psf.plot(pixel_scale)
