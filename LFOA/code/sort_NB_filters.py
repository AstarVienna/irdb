import numpy as np
from astropy.io import ascii
from astropy.table import Table
from matplotlib import pyplot as plt

filt_names = ["Halpha_narrow", "Halpha_wide", "Hbeta", "OIII", "SII"]
fnames = [f"../filters/TC_filter_{name}.dat" for name in filt_names]
for fname in fnames:
    tbl = ascii.read(fname)

    trans = tbl["transmission"] * 0.01
    wave = tbl["wavelength"] * 0.001

    trans[trans < 1e-5] = 0
    trans[trans > 1] = 1

    trans = trans[::-1]
    wave = wave[::-1]

    new_wave = np.arange(0.3, 1, 0.001)
    new_trans = np.interp(new_wave, wave, trans)

    new_tbl = Table(data=[new_wave, new_trans],
                    names=["wavelength", "transmission"],
                    meta=tbl.meta)
    new_tbl.meta["comments"] += []

    new_tbl.write(fname.replace(".dat", "_new.dat"), format="ascii.basic",
                  overwrite=True)
    #
    # plt.semilogy(new_tbl["wavelength"], new_tbl["transmission"])
    # plt.show()

    # print(new_tbl, len(new_tbl))