import os
import glob
import warnings

import numpy as np
from astropy.io import fits


def check_all_psf_files_have_correct_header_keywords_in_exts():
    psf_files = glob.glob("C:\Work\irdb\_PSFs\*.fits")

    ext_keys = ["CDELT1", "CDELT2", "CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2",
                "CUNIT1", "CUNIT2", "CTYPE1", "CTYPE2", "WAVE0", "PIXELSCL"]
    ext_keys_arr = np.array(ext_keys)

    incomplete_pfs_files = {}

    for fname in psf_files:
        with fits.open(fname) as hdulist:
            for ext, hdu in enumerate(hdulist):
                if isinstance(hdu, (fits.ImageHDU, fits.PrimaryHDU)) and \
                        hdu.data is not None and "CATTYPE" not in hdu.header:
                    key_mask = [key in hdu.header for key in ext_keys]
                    if not all(key_mask):
                        inv_mask = np.invert(key_mask)
                        ext_name = "{}[{}]".format(fname, ext)
                        missing_keys = ext_keys_arr[inv_mask]
                        msg = "{} is missing keywords: {}" \
                              "".format(ext_name, missing_keys)
                        warnings.warn(msg)

                        incomplete_pfs_files[ext_name] = list(missing_keys)

    return incomplete_pfs_files


def test_psf_fits_headers():
    if os.environ["USERNAME"] == "Kieran":
        psf_dict = check_all_psf_files_have_correct_header_keywords_in_exts()
        assert len(psf_dict) == 0
