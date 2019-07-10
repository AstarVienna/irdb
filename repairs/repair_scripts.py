import glob
from astropy.io import fits


def repair_fits_headers(filename):
    with fits.open(filename, mode="update") as hdulist:
        for hdu in hdulist:

            keys = ["CDELT1", "CDELT2", "CDELT1", "CDELT2", "PIXELSCL", "WAVE0"]
            keys_inv = ["CD1_1", "CD2_2", "PIXELSCL", "PIXELSCL", "CDELT1",
                        "WAVELENG"]
            for key, key_inv in zip(keys, keys_inv):
                if key not in hdu.header and key_inv in hdu.header:
                    hdu.header[key] = hdu.header[key_inv]

            if isinstance(hdu, (fits.PrimaryHDU, fits.ImageHDU)) and \
                    hdu.data is not None:
                missing_keys = ["CRVAL1", "CRVAL2", "CTYPE1", "CTYPE2",
                                "CRPIX1", "CRPIX2", 'CUNIT1', 'CUNIT2']
                missing_vals = [0, 0, "RA---TAN", "DEC--TAN",
                                hdu.data.shape[0] / 2., hdu.data.shape[1] / 2.,
                                "arcsec", "arcsec"]

                for key, val in zip(missing_keys, missing_vals):
                    if key not in hdu.header:
                        hdu.header[key] = val

        hdulist.flush()


psf_files = glob.glob("C:\Work\irdb\_PSFs\*.fits")
for fname in psf_files:
    repair_fits_headers(fname)
