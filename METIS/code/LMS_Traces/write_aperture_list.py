"""
Script to convert Alistair Glasse's LMS distortion files to FITS

The file requires two input files defined as WCAL_FILE and POLY_FILE below.
The output is a FITS file named TRACE_LMS.fits.
"""
import numpy as np
from astropy.io import fits
from astropy.io import ascii as ioascii

NSLICE = 28
SLITLENGTH = 109.4  # originally 122
SLICEWIDTH = 0.0207
PIXSCALE = 0.0082

WCAL_FILE = "lms_dist_wcal.txt"
POLY_FILE = "lms_dist_poly.txt"

def aperture_list():
    slice_id = np.arange(NSLICE) + 1
    xi_max = np.array([SLITLENGTH * PIXSCALE / 2] * NSLICE)
    xi_min = -xi_max
    eta_min = (np.arange(NSLICE) - NSLICE / 2) * SLICEWIDTH
    eta_max = eta_min + SLICEWIDTH
    angle = np.array([0] * NSLICE)
    conserve_image = [True] * NSLICE
    shape = ["rect"] * NSLICE

    hdu = fits.BinTableHDU.from_columns(
        [fits.Column(name='id', format='I2', array=slice_id),
         fits.Column(name='left', format='F.4', array=xi_min, unit="arcsec"),
         fits.Column(name='right', format='F.4', array=xi_max, unit="arcsec"),
         fits.Column(name='top', format='F.4', array=eta_max, unit="arcsec"),
         fits.Column(name='bottom', format='F.4', array=eta_min, unit="arcsec"),
         fits.Column(name='angle', format='F.1', array=angle, unit="deg"),
         fits.Column(name='conserve_image', format='A4', array=conserve_image),
         fits.Column(name='shape', format='A6', array=shape)
         ])
    hdu.header['EXTNAME'] = "Aperture List"
    hdu.header['DESCRIPT'] = "Aperture List for METIS LMS, nominal mode"
    hdu.header['X_UNIT'] = "arcsec"
    hdu.header['Y_UNIT'] = "arcsec"
    hdu.header['ANGLE_UNIT'] = "deg"
    return hdu

def wcal():
    wcal = ioascii.read(WCAL_FILE, comment="^#", format="csv")
    wcal['c0'].unit = "deg / um"
    wcal['c1'].unit = "deg"
    wcal['ic0'].unit = "um / deg"
    wcal['ic1'].unit = "um"
    hdu = fits.table_to_hdu(wcal)
    hdu.header['EXTNAME'] = "WCAL"
    return hdu


def poly():
    poly = ioascii.read(POLY_FILE, comment="^#", format="csv")
    hdu = fits.table_to_hdu(poly)
    hdu.header['EXTNAME'] = "Polynomial coefficients"
    return hdu

def catalogue():
    desc = fits.Column(name="description", format="10A",
                       array=["APERTURE", "WCAL", "POLY"])
    ext_id = fits.Column(name="extension_id", format="I",
                         array=[2, 3, 4])
    aperture_id = fits.Column(name="aperture_id", format="I",
                              array=[0, 0, 0])
    image_plane_id = fits.Column(name="image_plane_id", format="I",
                                 array=[0, 0, 0])
    hdu = fits.BinTableHDU.from_columns([desc, ext_id, aperture_id, image_plane_id])
    hdu.header['EXTNAME'] = "Catalogue"
    return hdu

if __name__ == "__main__":

    pheader = fits.Header()
    pheader['AUTHOR'] = "Oliver Czoske"
    pheader['DATE'] = '2021-09-08'
    pheader['ORIGDATE'] = '2021-09-08'
    pheader['STATUS'] = 'Design'
    pheader['SOURCE'] = "E-REP-ATC-MET-1003_2-0, E-REP-ATC-MET-1016_1-0"
    pheader['DESCRIPT'] = "METIS LMS trace layout and slice definition"
    pheader['DATE_CRE'] = "2021-09-08"
    pheader['DATE_MOD'] = "2025-08-12"
    pheader['FILETYPE'] = "Spectral Layout Definition"
    pheader['ECAT'] = 1
    pheader['EDATA'] = 2

    primary_hdu = fits.PrimaryHDU(header=pheader)
    catalogue_hdu = catalogue()
    aperture_hdu = aperture_list()
    wcal_hdu = wcal()
    poly_hdu = poly()
    hdul = fits.HDUList([primary_hdu,
                         catalogue_hdu,
                         aperture_hdu,
                         wcal_hdu,
                         poly_hdu])
    hdul.writeto("TRACE_LMS.fits", overwrite=True)
