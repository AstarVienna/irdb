import numpy as np
from astropy.io import fits
from astropy.table import Table

hdul = fits.open("../TRACE_MICADO_Feb2022.fits")

for i in range(2, len(hdul)):
    tbl = Table(hdul[i].data)
    ids = np.argwhere((tbl["xi"] == 0) +
                      # (abs(tbl["x"]) > 103) +
                      (abs(tbl["y"]) > 103))
    tbl.remove_rows(ids)
    hdu_new = fits.table_to_hdu(tbl)
    for key in ['EXTNAME', 'WAVECOLN', 'SLITPOSN']:
        hdu_new.header[key] = hdul[i].header[key]
    for key in hdul[i].header:
        if "TUNIT" in key:
            hdu_new.header[key] = hdul[i].header[key]

    hdul[i] = hdu_new

hdul.writeto("../TRACE_MICADO.fits", overwrite=True)
