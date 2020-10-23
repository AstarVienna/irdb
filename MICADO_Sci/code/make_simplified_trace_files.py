from astropy.io import fits
from astropy.table import Table
import numpy as np


def make_hdulist_fits_file():

    pri_hdu = fits.PrimaryHDU()
    meta = {"ECAT": 1,
            "EDATA": 2}
    pri_hdu.header.update(meta)

    names = ["description", "extension_id", "aperture_id", "image_plane_id"]
    data = [["IJ", "HK"], [2, 3], [0, 0], [0, 0]]
    cat_tbl = Table(names=names, data=data)
    cat_hdu = fits.table_to_hdu(cat_tbl)

    names = ["wavelength", "s0", "s1", "x0", "x1", "y0", "y1"]
    data = []

    ij_tbl = None


def make_waves_ys():
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
    # import matplotlib.pyplot as plt
    # plt.plot(ws[ws>=0.78], dys[ws>=0.78])
    # plt.show()

    return ws, ys


print(make_waves_ys())