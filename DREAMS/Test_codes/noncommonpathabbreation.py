import os
import warnings
import numpy as np
from astropy import units as u
from astropy.convolution import Gaussian2DKernel
from scopesim.utils import from_currsys, quantify, quantity_from_table, figure_factory, check_keys
from scopesim.base_classes import ImagePlaneBase, FieldOfViewBase
from scopesim.effects import PSF, PoorMansFOV

from astropy.io.fits import HDUList
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import scopesim
from scopesim.utils import quantify
from scopesim import rc
from scopesim_templates.stellar import star_field, star_grid
from scopesim.optics.fov_manager import FOVManager



print("Done with all the library installation")

PLOTS = True

class AnalyticalPSF(PSF):
    """Base class for analytical PSFs."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.meta["z_order"] = [41, 641]
        self.convolution_classes = FieldOfViewBase


class NonCommonPathAberration(AnalyticalPSF):
    """
    Non-Common Path Aberration class.

    Needed: pixel_scale
    Accepted: kernel_width, strehl_drift
    """

    required_keys = {"pixel_scale"}

    def __init__(self, diameter, wave_min, wave_max, pixel_scale, **kwargs):
        super().__init__(**kwargs)
        self.meta["z_order"] = [241, 641]
        self.meta["kernel_width"] = None
        self.meta["strehl_drift"] = 0.02
        self.meta["wave_min"] = wave_min  # Set the wave_min directly
        self.meta["wave_max"] = wave_max  # Set the wave_max directly

        self._total_wfe = None
        self.valid_waverange = [wave_min * u.um, wave_max * u.um]

        self.convolution_classes = FieldOfViewBase
        check_keys(self.meta, self.required_keys, action="error")

    def get_kernel(self, pixel_scale):
        waves = (self.meta["wave_min"], self.meta["wave_max"])

        old_waves = self.valid_waverange
        wave_mid_old = 0.5 * (old_waves[0] + old_waves[1])
        wave_mid_new = 0.5 * (waves[0] + waves[1])
        strehl_old = wfe2strehl(wfe=self.total_wfe, wave=wave_mid_old)
        strehl_new = wfe2strehl(wfe=self.total_wfe, wave=wave_mid_new)

        if np.abs(1 - strehl_old / strehl_new) > self.meta["strehl_drift"]:
            self.valid_waverange = waves
            self.kernel = wfe2gauss(wfe=self.total_wfe, wave=wave_mid_new,
                                    width=self.meta["kernel_width"])
            self.kernel /= np.sum(self.kernel)

        return self.kernel

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
        plt.imshow(kernel, origin='lower', extent=[x[0], x[-1], y[0], y[-1]], cmap='plasma', norm=LogNorm(vmin=1e-6, vmax=1))  # Adjust vmin and vmax as necessary
        plt.colorbar(label='Intensity')
        plt.title(f"Non-Common Path Aberration PSF (Diameter = {diameter} m)")
        plt.xlabel("X [arcseconds]")
        plt.ylabel("Y [arcseconds]")
        plt.gca().set_aspect('equal', adjustable='box')  # Equal aspect ratio
        plt.grid(False)  # Optional: disable grid for clarity
        plt.show()

# Rest of your setup code...

# Initialize the NonCommonPathAberration class
npc_psf = NonCommonPathAberration(
    diameter=0.5,
    wave_min=0.01161,
    wave_max=0.01333,
    pixel_scale=2.48
)

# Plot the Aberration affected PSF
npc_psf.plot(pixel_scale=2.48)

