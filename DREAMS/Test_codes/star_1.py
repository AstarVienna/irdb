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
cmds["!OBS.dit"] = 10
cmds["!DET.bin_size"] = 1
cmds["!OBS.sky.bg_mag"] = 14.9
cmds["!OBS.sky.filter_name"] = "J"
cmds["SIM.sub_pixel.flag"] = True
dreams = scopesim.OpticalTrain(cmds)
dreams["detector_linearity"].include = False

print("scopesim package loaded successfully.")
x, y = np.meshgrid(np.arange(100), np.arange(100))
img = np.exp(-1 * ( ( (x - 50) / 5)**2 + ( (y - 50) / 5)**2 ) )
# Fits headers of the image. Yes it needs a WCS
hdr = fits.Header(dict(NAXIS=2,NAXIS1=img.shape[0]+1,NAXIS2=img.shape[1]+1, CRPIX1=img.shape[0] / 2, CRPIX2=img.shape[1] / 2, CRVAL1=0, CRVAL2=0, CDELT1=0.2/3600, CDELT2=0.2/3600,
CUNIT1="DEG", CUNIT2="DEG", CTYPE1='RA---TAN', CTYPE2='DEC--TAN'))
# Creating an ImageHDU object
hdu = fits.ImageHDU(data=img, header=hdr)

# Creating of a black body spectrum
wave = np.arange(1000, 35000, 10 )
bb = synphot.models.BlackBody1D(temperature=5000)
sp = synphot.SourceSpectrum(synphot.Empirical1D, points=wave, lookup_table=bb(wave))
src = Source(image_hdu=hdu, spectra=sp)
src.shift(10, 10)
dreams.observe(src)
print("yessss anjali")
hdus = dreams.readout()
#dreams.readout(filename="Han.fits")
plt.subplot(121)
wave = np.arange(3000, 11000)
plt.plot(wave, dreams.optics_manager.system_transmission(wave))
plt.subplot(122)
im = hdus[0][1].data
detector_order = [2, 1, 4, 3, 6, 5]
plt.figure(figsize=(20, 20))
for plot_number, hdu_number in enumerate(detector_order, 1):
    plt.subplot(3, 2, plot_number)
    plt.imshow(hdus[0][hdu_number].data, origin="lower", norm=LogNorm())
    plt.colorbar()
  
plt.show()
