import numpy as np
from scipy.ndimage import zoom
from astropy.io import fits


def rescale_image(old_hdu, new_cdelt, max_size=512):
    scale_factor = old_hdu.header["CDELT1"] / new_cdelt
    image = zoom(old_hdu.data, scale_factor)

    print(image.shape[0] * new_cdelt)

    image /= image.sum()
    y, x = np.divmod(np.argmax(image), image.shape[1])
    r = max_size // 2
    x0, x1 = x - r, x + r
    y0, y1 = y - r, y + r
    image = image[y0:y1, x0:x1]
    y, x = np.divmod(np.argmax(image), image.shape[1])

    new_hdu = fits.ImageHDU(data=image, header=old_hdu.header)
    new_hdu.header["CDELT1"] = new_cdelt
    new_hdu.header["CDELT2"] = new_cdelt
    new_hdu.header["CRPIX1"] = x
    new_hdu.header["CRPIX2"] = y
    new_hdu.header["PIXSCALE"] = new_cdelt

    return new_hdu


def build_new_psf_file(max_size=512, save=False):
    old_hdul = fits.open("../PSF_SCAO_9mag_06seeing.fits")
    new_hdul = fits.HDUList()
    new_hdul.append(fits.PrimaryHDU())
    new_hdul.append(rescale_image(old_hdul[2], 5.47, max_size))
    new_hdul.append(rescale_image(old_hdul[3], 6.79, max_size))
    new_hdul.append(rescale_image(old_hdul[4], 6.79, max_size))
    new_hdul.append(rescale_image(old_hdul[5], 6.79, max_size))

    for i in range(1, 5):
        new_hdul[0].header[f"WAVE{i}"] = new_hdul[i].header["WAVELENG"], "um"

    old_keys = {"FILETYPE": "Point Spread Functions",
                "AUTHOR"  : "Oliver Czoske",
                "DATE"    : "2018-10-09",
                "SOURCE"  : "Markus Feldt, MPIA",
                "ORIGDATE": "2018-??-??"}
    new_hdul[0].header.update(old_keys)

    for history in ["CHANGES:",
                    "- 2018-10-09: [OC] Formatted for ScopeSim",
                    "- 2021-12-07: [KL] Rescaled to METIS detector pixel scales"]:
        new_hdul[0].header["HISTORY"] = history

    if save:
        new_hdul.writeto("PSF_SCAO_9mag_06seeing_rescaled.fits")

    return new_hdul


def check_sum_of_kernels():
    hdul = build_new_psf_file(1024)
    for i in range(1, len(hdul)):
        print(hdul[i].header["WAVELENG"], hdul[i].data.sum())


check_sum_of_kernels()
