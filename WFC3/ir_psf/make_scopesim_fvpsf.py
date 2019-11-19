# data pulled from: http://www.stsci.edu/hst/instrumentation/wfc3/data-analysis/psf
# each cube has a 3x3 matrix

import numpy as np
from astropy.io import fits
from astropy.table import Table

plate_scale = 0.13
x = np.array([-507, 0, 507]*3)
y = np.array([-507]*3 + [0]*3 + [507]*3)
i = np.arange(len(x))
tbl = Table(data=[x,y,i], names=["x", "y", "layer"])

pri_hdu = fits.PrimaryHDU()
pri_hdu.header["AUTHOR"] = "Kieran Leschinski"
pri_hdu.header["DATE_CRE"] = "2019-11-19"
pri_hdu.header["DATE_MOD"] = "2019-11-19"
pri_hdu.header["SOURCE"] = "http://www.stsci.edu/hst/instrumentation/wfc3/data-analysis/psf"
pri_hdu.header["STATUS"] = "Measured"
pri_hdu.header["ETYPE"] = "FVPSF"
pri_hdu.header["ECAT"] = 1
pri_hdu.header["EDATA"] = 2

tbl_hdu = fits.table_to_hdu(tbl)
tbl_hdu.header["NUMPSFS"] = 9
tbl_hdu.header["CATTYPE"] = "table"
tbl_hdu.header["CUNIT1"] = "arcsec"

psf_hdus = []
for wave in [105, 110, 125, 140, 160]:
    filename = "PSFSTD_WFC3IR_F{}W.fits".format(wave)
    imhdu = fits.ImageHDU(fits.getdata(filename))
    imhdu.header["WAVE0"] = (wave / 100., "[um] Wavelength")
    imhdu.header["WAVELENG"] = (wave / 100., "[um] Wavelength")
    imhdu.header["WAVEUNIT"] = "um"
    imhdu.header["CTYPE1"] = "RA---TAN"
    imhdu.header["CTYPE2"] = "DEC--TAN"
    imhdu.header["CUNIT1"] = "arcsec"
    imhdu.header["CUNIT2"] = "arcsec"
    imhdu.header["CRVAL1"] = 0
    imhdu.header["CRVAL2"] = 0
    imhdu.header["CRPIX1"] = 507
    imhdu.header["CRPIX2"] = 507
    imhdu.header["CDELT1"] = 0.0325
    imhdu.header["CDELT2"] = 0.0325

    psf_hdus += [imhdu]

wfc3_ir_fvpsf = fits.HDUList([pri_hdu, tbl_hdu] + psf_hdus)
wfc3_ir_fvpsf.writeto("../PSF_WFC3_IR_FV.fits", overwrite=True)
