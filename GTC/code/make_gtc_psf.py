from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from scipy.signal import fftconvolve

import poppy
from astropy.io import fits
from astropy.convolution import Gaussian2DKernel

PLOTS = False

def make_poppy_psf():

    n_pixels = 128
    pixel_scale = 0.114
    wavelength = 0.5
    seeing = 0.67

    ap = poppy.MultiHexagonAperture(rings=3, flattoflat=1.64)           # 3 rings of 2 m segments yields 14.1 m circumscribed diameter
    # outer = poppy.CircularAperture(radius=4.5, name="Entrance Pupil")   # secondary with spiders
    inner = poppy.SecondaryObscuration(secondary_radius=0.9, n_supports=6, support_width=0.1)   # secondary with spiders
    gtc_pupil = poppy.CompoundAnalyticOptic( opticslist=[ap, inner], name='GTC Pupil')           # combine into one optic

    ax = plt.subplot(221)
    gtc_pupil.display(npix=1024, ax=ax, colorbar=False)

    osys = poppy.OpticalSystem()
    osys.add_pupil(gtc_pupil)
    osys.add_detector(pixelscale=pixel_scale, fov_arcsec=pixel_scale * n_pixels)
    psf = osys.calc_psf(wavelength * 1e-6)

    plt.subplot(222)
    # poppy.display_psf(psf, title="Mock ATLAST PSF")
    plt.imshow(psf[0].data)

    fwhm = seeing / pixel_scale
    sigma = fwhm / 2.355
    kernel = Gaussian2DKernel(sigma)

    plt.subplot(223)
    plt.imshow(kernel)

    psf2 = fftconvolve(psf[0].data, kernel)
    plt.subplot(224)
    plt.imshow(psf2, norm=LogNorm())

    if PLOTS:
        plt.show()

    #######################

    pri_hdu = fits.PrimaryHDU()
    pri_hdu.header["EDATA"] = 1
    hdus = []
    waves = [0.4, 0.6, 0.9]
    for i, wave in enumerate(waves):
        pri_hdu.header[f"WAVE{i+1}"] = (wave, "[um]")

        psf_hdu = osys.calc_psf(wavelength * 1e-6)
        psf_hdu[0].data = fftconvolve(psf_hdu[0].data, kernel)

        psf_hdu[0].header["WAVE0"] = (wave, "Wavelength [um]")
        psf_hdu[0].header["WAVEUNIT"] = "um"
        psf_hdu[0].header["CDELT1"] = (pixel_scale / 3600, "Pixel scale [deg]")
        psf_hdu[0].header["CDELT2"] = (pixel_scale / 3600, "Pixel scale [deg]")
        psf_hdu[0].header["CUNIT1"] = "DEGREE"
        psf_hdu[0].header["CUNIT2"] = "DEGREE"
        psf_hdu[0].header["CRVAL1"] = 0
        psf_hdu[0].header["CRVAL2"] = 0
        psf_hdu[0].header["CRREF1"] = psf_hdu[0].header["NAXIS1"] / 2
        psf_hdu[0].header["CRREF2"] = psf_hdu[0].header["NAXIS2"] / 2

        img_hdu = fits.ImageHDU(data=psf_hdu[0].data, header=psf_hdu[0].header)
        hdus += [img_hdu]

    hdus = [pri_hdu] + hdus

    hdulist = fits.HDUList(hdus)
    hdulist.writeto("GTC_poppy_PSF.fits")


def shrink_osiris_psf():
    # hdu = fits.open("psf_osiris_r.fits")
    # hdu[0].header["PIXELSCL"] = 1 # hdu[0].header["CD1_1"] * -3600
    # hdu[0].data /= hdu[0].data.sum()
    # poppy.display_profiles(hdu)
    # plt.plot([1, 1])
    # plt.show()
    #
    # Source file
    # http://www.gtc.iac.es/instruments/osiris/media/psf_osiris_r.fits.gz
    import numpy as np
    hdu_orig = fits.open("psf_osiris_r.fits")

    # plt.imshow(hdu_orig[0].data, norm=LogNorm())
    # plt.show()

    data = hdu_orig[0].data
    data /= data.sum()
    hdr = hdu_orig[0].header
    x, y = np.divmod(np.argmax(data), data.shape[0])
    r = 512
    data = data[y-r:y+r, x-r:x+r]

    cdelt1 = np.sqrt(hdr["CD1_1"]**2 + hdr["CD2_1"]**2)
    cdelt2 = np.sqrt(hdr["CD1_2"]**2 + hdr["CD2_2"]**2)

    hdu = fits.ImageHDU(data=data)
    hdu.header["WAVE0"] = (0.65, "Wavelength [um]")
    hdu.header["WAVEUNIT"] = "um"
    hdu.header["CDELT1"] = (cdelt1, "Pixel scale [deg]")
    hdu.header["CDELT2"] = (cdelt2, "Pixel scale [deg]")
    hdu.header["CUNIT1"] = "deg"
    hdu.header["CUNIT2"] = "deg"
    hdu.header["CRVAL1"] = 0
    hdu.header["CRVAL2"] = 0
    hdu.header["CRPIX1"] = (hdu.header["NAXIS1"] + 1) / 2
    hdu.header["CRPIX2"] = (hdu.header["NAXIS2"] + 1) / 2
    hdu.header["CTYPE1"] = "LINEAR"
    hdu.header["CTYPE2"] = "LINEAR"

    pri_hdu = fits.PrimaryHDU()
    pri_hdu.header["EDATA"] = 1
    pri_hdu.header["ECAT"] = -1
    pri_hdu.header["SOURCE"] = "http://www.gtc.iac.es/instruments/osiris/media/psf_osiris_r.fits.gz"
    pri_hdu.header["DATE_CRE"] = "2022-02-18"
    pri_hdu.header["DATE_MOD"] = "2022-02-18"
    pri_hdu.header["AUTHOR"] = "Kieran Leschinski"

    hdul = fits.HDUList([pri_hdu, hdu])
    hdul.writeto("PSF_GTC_OSIRIS.fits", overwrite=True)


shrink_osiris_psf()
