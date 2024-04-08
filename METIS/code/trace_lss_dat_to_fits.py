from astropy import units as u
from astropy.table import Table
from astropy.io import fits, ascii
import matplotlib.pyplot as plt

from pathlib import Path
from os import path as pth
from glob import glob
import numpy as np


def make_pri_hdu():
    pri_hdu = fits.PrimaryHDU()
    pri_hdu.header["ECAT"] = 1
    pri_hdu.header["EDATA"] = 2

    meta = {"author": "Kieran Leschinski",
            "source": "Conchi Cardenas Vazquez",
            "descript": "METIS L-band LSS Spectral Trace. Final version",
            "date-cre": "2023-06-20",
            "date-mod": "2024-04-08",
            "status": "Ready for Manufacturing"
            }
    pri_hdu.header.update(meta)

    return pri_hdu


def make_cat_hdu(file_names):
    trace_names = [path.stem for path in file_names]
    cat_table = Table(data=[trace_names,
                            list(2 + np.arange(len(trace_names))),
                            [0]*len(trace_names),
                            [0]*len(trace_names)
                            ],
                      names=["description", "extension_id",
                             "aperture_id", "image_plane_id"])
    cat_hdu = fits.table_to_hdu(cat_table)
    cat_hdu.header["EXTNAME"] = "TOC"

    return cat_hdu


def make_spec_trace_hdu(file_paths):
    # NOTE : Data is delivered with x,y=(0,0) being the bottom-left corner
    #   need to change this to x,y=(0,0) at pixel coord (1024,1024)

    pixel_size = 0.018  # mm
    dx, dy = [pixel_size * 1024] * 2

    trace_hdus = []
    for path in file_paths:
        data = ascii.read(path.name, fast_reader=True)
        for i, unit_str in enumerate(["um", "arcsec", "mm", "mm"]):
            data.columns[i].unit = u.Unit(unit_str)
        data["x"] -= dx
        data["y"] -= dy
        table_hdu = fits.table_to_hdu(data)
        table_hdu.header["EXTNAME"] = path.stem
        table_hdu.header["DISPDIR"] = "y"

        trace_hdus += [table_hdu]

        # plt.scatter(data["x"], data["y"], c=data["wavelength"])
        # plt.show()

    return trace_hdus


def do_main(filter_name = "L"):
    dir_path = Path(".")
    filenames = [fn for fn in dir_path.glob(f"*{filter_name}_band.dat")]

    pri_hdu = make_pri_hdu()
    cat_hdu = make_cat_hdu(filenames)
    trace_hdus = make_spec_trace_hdu(filenames)

    trace_hdulist = fits.HDUList([pri_hdu] + [cat_hdu] + trace_hdus)
    trace_hdulist.writeto(f"TRACE_LSS_{filter_name}.fits", overwrite=True)


if __name__ == '__main__':
    do_main("L")
    do_main("M")
    do_main("N")
