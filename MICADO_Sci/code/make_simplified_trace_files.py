from astropy.io import fits
from astropy.table import Table
from astropy import units as u
import numpy as np
import matplotlib.pyplot as plt


def make_waves_and_ys():
    waves = {int(np.round(wave, 2) * 1000): None for wave in np.arange(0.60, 2.51, 0.01)}
    hdulist = fits.open("../../MICADO/TRACE_3arcsec.fits")
    for ext in hdulist[2:]:
        for i, lam in enumerate(ext.data["lam"][:-1]):
            dy = -np.diff(ext.data["y2"][i:i + 2])[0]
            w = int(np.round(lam, 2) * 1000)
            if dy > 0:
                if waves[w] is None:
                    waves[w] = dy
                elif dy < waves[w]:         # flip < if we want best case scenario
                    waves[w] = dy

    ws = np.array(list(waves.keys())) / 1000.
    dys = np.array(list(waves.values()))

    dys[0] = 0
    for i in range(1, len(dys)):
        if dys[i] is None:
            dys[i] = dys[i-1]

    ys = np.cumsum(np.array(dys))

    # plt.plot(ws[ws>=0.78], dys[ws>=0.78])

    return ws, ys


def make_trace_table(wave_min, wave_max, width=3):

    waves, ys = make_waves_and_ys()
    mask = (waves >= wave_min) * (waves <= wave_max)
    waves = waves[mask] * u.um
    ys = ys[mask] * u.mm

    n = len(waves)
    xs = np.ones(n) / 0.004 * 0.015 * u.mm
    ss = np.ones(n) * u.arcsec

    names = ["wavelength",
             "s0", "s1",
             "x0", "x1",
             "y0", "y1"]
    data = [waves,
            -0.5 * width * ss, 0.5 * width * ss,
            -0.5 * width * xs, 0.5 * width * xs,
            ys, ys]
    tbl = Table(names=names, data=data)

    return tbl


def make_hdulist_fits_file(width=3):
    pri_hdu = fits.PrimaryHDU()
    meta = {"ECAT": 1,
            "EDATA": 2}
    pri_hdu.header.update(meta)

    # names = ["description", "extension_id", "aperture_id", "image_plane_id"]
    # data = [["IJ", "HK"], [2, 3], [0, 0], [0, 0]]
    # cat_tbl = Table(names=names, data=data)
    # cat_hdu = fits.table_to_hdu(cat_tbl)
    # cat_hdu.header["EXTNAME"] = "CAT_TRAC"

    # ij_tbl = make_trace_table(0.75, 1.5, width)
    # ij_hdu = fits.table_to_hdu(ij_tbl)
    # ij_hdu.header["EXTNAME"] = "IJ_TRACE"
    #
    # hk_tbl = make_trace_table(1.40, 2.5, width)
    # hk_hdu = fits.table_to_hdu(hk_tbl)
    # hk_hdu.header["EXTNAME"] = "HK_TRACE"
    #
    # hdu_list = fits.HDUList([pri_hdu, cat_hdu, ij_hdu, hk_hdu])

    names = ["description", "extension_id", "aperture_id", "image_plane_id"]
    data = [["IJHK"], [2], [0], [0]]
    cat_tbl = Table(names=names, data=data)
    cat_hdu = fits.table_to_hdu(cat_tbl)
    cat_hdu.header["EXTNAME"] = "CAT_TRAC"

    ijhk_tbl = make_trace_table(0.75, 2.5, width)
    ijhk_hdu = fits.table_to_hdu(ijhk_tbl)
    ijhk_hdu.header["EXTNAME"] = "IJHK"

    hdu_list = fits.HDUList([pri_hdu, cat_hdu, ijhk_hdu])

    return hdu_list


# for width in [3, 15]:
#     hdu_list = make_hdulist_fits_file(width)
#     hdu_list.writeto(f"TRACE_SCI_{width}arcsec.fits", overwrite=True)

waves, ys = make_waves_and_ys()
plt.plot(waves[1:], np.diff(ys))
plt.show()
