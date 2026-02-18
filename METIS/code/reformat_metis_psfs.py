"""Reformat RvB's PSF cubes for use in scopesim

- scopesim uses multiextension fits files with a single PSF image per extension
- CUNIT3 "micrometer" replaced by "um"

Author: Oliver Czoske
Date:   2025-11-24
"""
import sys
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

def reformat_file(infile):
    """Convert the file `infile`"""
    with fits.open(infile) as hdul:
        nwave = hdul[0].data.shape[0]
        crval = hdul[0].header["CRVAL3"]
        cdelt = hdul[0].header["CDELT3"]
        # Fix some header keywords
        if hdul[0].header["CUNIT3"] == "micrometer":
            hdul[0].header["CUNIT3"] = "um"
        else:
            print("What?", hdul[0].header["CUNIT3"])
        if "CTYPE1" not in hdul[0].header or hdul[0].header["CTYPE1"] == "":
            hdul[0].header["CTYPE1"] = "LINEAR"
            hdul[0].header["CTYPE2"] = "LINEAR"

        wavelengths = np.exp(crval + cdelt * np.arange(1, nwave+1))

        wcs = WCS(hdul[0].header).sub(2)
        phdu = fits.PrimaryHDU()
        phdu.header["FILETYPE"] = "Point Spread Functions"
        phdu.header["AUTHOR"] = "Roy van Boekel, Oliver Czoske"
        phdu.header["DATE"] = "2025-11-24"
        phdu.header["ORIGDATE"] = "2025-10-30"
        phdu.header["ORIGFILE"] = (Path(infile).name, "original file name")
        phdu.header["COLDSTOP"] = (hdul[0].header["COLDSTOP"], "name cold pupil mask")
        if "WCU" in infile:
            phdu.header["ELTMASK"] = False
            wcustr = "_WCU"
        else:
            phdu.header["ELTMASK"] = True
            wcustr = ""
        phdu.header["PUPILPS"] = (hdul[0].header["PUPILPS"], "[mm] pupil model pixel size")
        phdu.header["NPIXFFT"] = (hdul[0].header["NPIXFFT"], "number of pixels used in FFT")
        phdu.header["PUPILPS"] = (hdul[0].header["OSAMP"], "over-sampling factor")
        phdu.header["PSIZEPUP"] = (hdul[0].header["PSIZEPUP"], "[mm] pixel size in pupil image")
        outhdul = fits.HDUList([phdu])
        if "IMG" in infile:
            substr = "IMG"
        elif "LMS" in infile:
            substr = "LMS"
        else:
            raise ValueError("Unknown subsystem")
        outfile = f"psfs/PSF_{substr}_{phdu.header['COLDSTOP']}{wcustr}.fits"
        for i in range(nwave):
            psfimg = hdul[0].data[i,]
            hdr = wcs.to_header()
            hdr['WAVELENG'] = (wavelengths[i], "[um] Wavelength of PSF image")
            hdr['WAVEUNIT'] = 'um'
            hdr['EXTNAME'] = f"PSF_{wavelengths[i]:.2f}um"

            hdu = fits.ImageHDU(data=psfimg, header=hdr)
            outhdul.append(hdu)
        outhdul.writeto(outfile, overwrite=True)


if __name__ == "__main__":
    infilelist = sys.argv[1:]

    for thefile in infilelist:
        reformat_file(thefile)
