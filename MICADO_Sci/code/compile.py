from os import path as pth
from datetime import date

import numpy as np
import matplotlib.pyplot as plt
from astropy import units as u
from astropy.table import Table
from astropy.io import fits

import anisocado as aniso
from scopesim import rc
from scopesim.effects import SurfaceList

PLOTS = False

MORFEO_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../../MORFEO/"))
rc.__search_path__.insert(0, MORFEO_DIR)
MICADO_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../../MICADO/"))
rc.__search_path__.insert(0, MICADO_DIR)
MICADO_SCI_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))


def compress_surface_list_to_ter(f_in, f_out, header_list=[], **kwargs):
    """
    A TERCurve (~5ms) is 100x faster than a SurfaceList (~500ms)

    Parameters
    ----------
    f_in, f_out : str
    header_list: list
    kwargs : dict
        params to pass to SurfaceList

    """

    sl = SurfaceList(filename=f_in, **kwargs)
    wave = np.arange(0.7, 2.5, 0.001) * u.um
    thru = sl.throughput(wave)
    flux = sl.emission(wave)
    flux[flux < 1e-32 * flux.unit] = 0.

    comments = ["author : Auto-compiled from source",
                "source : {}".format(f_in),
                "description : SurfaceList collapsed into single TERCurve",
                "date_created : {}".format(str(date.today())),
                "date_modified : {}".format(str(date.today())),
                "area : {}".format(sl.area.value),
                "area_unit : m2",
                "wavelength_unit : um",
                "emission_unit : photlam"]
    comments += header_list

    tbl = Table(data=(wave, thru, flux),
                names=("wavelength", "transmission", "emission"))
    tbl.meta["comments"] = comments
    tbl.write(filename=pth.join(MICADO_SCI_DIR, f_out),
              format="ascii.fixed_width", delimiter=" ")


rc.__currsys__["!ATMO.temperature"] = 0
kwargs = {"etendue": 978*u.m**2 * (0.004*u.arcsec)**2}

# MICADO common optics
compress_surface_list_to_ter(f_in="LIST_MICADO_mirrors_static.dat",
                             f_out="TER_MICADO_IMG_common.dat", **kwargs)

# RO common optics
compress_surface_list_to_ter(f_in="LIST_RO_SCAO_mirrors.dat",
                             f_out="TER_MICADO_RO.dat", **kwargs)

# MORFEO common optics
compress_surface_list_to_ter(f_in="LIST_mirrors_morfeo_mms.tbl",
                             f_out="TER_MORFEO_MMS.dat", **kwargs)


def generate_anisocado_strehl_map_for_micado():
    # 310 nm --> 40 in Ks, 18 in H, 6 in J
    nmRms = np.linspace(0, 700, 36)
    waves = np.linspace(0.8, 2.4, 9)
    offset = [0, 0]
    psfs = []
    srs = np.zeros((len(nmRms), len(waves)))
    for y, wave in enumerate(waves):
        sr = 1
        for x, rms in enumerate(nmRms):
            if sr > 0.001:
                psf = aniso.AnalyticalScaoPsf(pixelSize=0.004, N=256,
                                              wavelength=wave, nmRms=rms)
                psf.shift_off_axis(offset[0], offset[1])
                psfs += [psf.hdu]
                sr = psf.strehl_ratio

            srs[x, y] = sr

            print(wave, rms, srs[x, y])

    hdu = fits.ImageHDU(data=srs)
    hdu.writeto("AnisoCADO_rms_map.fits", clobber=True)

    plt.imshow(srs)
    plt.colorbar()
    plt.show()
