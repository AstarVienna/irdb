"""Compute IFU mean dispersion as a function of central wavelength

The LineSpreadFunction effect needs the dispersion dlam_per_pix on
the LMS detector to determine the width of the LSF kernel to be
applied to the cube in mode `lms_cube`. The script computes the mean
dispersion as (lam_max - lam_min)/4220 for a number of wavelength settings,
and then performs a linear regression of dlam_per_pix against wavelength.
LineSpreadFunction() uses the slope and intercept to get a sufficient
approximation to the dispersion without having to reference TRACE_LMS.fits
or instantiate MetisLMSSpectralTraces itself.
"""
# Author: Oliver Czoske
# Date:   2025-05-21

import numpy as np
from scipy.stats import linregress
from matplotlib import pyplot as plt
import scopesim as sim

if __name__ == "__main__":
    sim.link_irdb("../../")    # from METIS/code/

    NPIX = 4220    # twice 2048 plus gap, from FPA_metis_lms_layout.dat
    wavelens = np.linspace(2.677, 5.332, 100)   # um
    dlam_per_pix = np.zeros_like(wavelens)

    for i, lamc in enumerate(wavelens):
        cmd = sim.UserCommands(use_instrument="METIS",
                               set_modes=["lms"],
                               properties={"!OBS.wavelen": lamc})
        metis = sim.OpticalTrain(cmd)
        splist = metis['lms_spectral_traces']
        lam_min = splist.meta['wave_min']
        lam_max = splist.meta['wave_max']

        dlam_per_pix[i] = (lam_max - lam_min) / NPIX

    linfit = linregress(wavelens, dlam_per_pix)
    slope = linfit.slope
    intercept = linfit.intercept
    print("Slope:    ", slope, "# um/pix")
    print("Intercept:", intercept, "# um")

    plt.plot(wavelens, dlam_per_pix, 'o')
    plt.plot(wavelens, intercept + slope * wavelens)
    plt.show()
