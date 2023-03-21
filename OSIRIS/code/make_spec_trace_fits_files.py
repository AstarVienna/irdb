from os import path as pth
from glob import glob
import numpy as np

from astropy.io import ascii
from astropy.io import fits
from astropy.table import Table
from astropy import units as u


def make_spec_trace_hdu(trace_names, dir_path, fname_format="{}.dat"):
    trace_hdus = []
    for name in trace_names:
        file_path = pth.join(dir_path, fname_format.format(name))
        data = ascii.read(file_path, format='basic', fast_reader=True)
        for i, unit_str in enumerate(["um", "arcsec", "mm", "mm"]):
            data.columns[i].unit = u.Unit(unit_str)
        table_hdu = fits.table_to_hdu(data)
        table_hdu.header["EXTNAME"] = name

        trace_hdus += [table_hdu]

        # plt.scatter(data["x"], data["y"], c=data["wavelength"])
        # plt.show()

    return trace_hdus


def make_cat_hdu(trace_names):
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


def make_pri_hdu():
    pri_hdu = fits.PrimaryHDU()
    pri_hdu.header["ECAT"] = 1
    pri_hdu.header["EDATA"] = 2

    meta = {"author": "David Jones",
            "source": "David Jones",
            "descript": "R1000B OSIRIS LSS Spectral Trace",
            "date-cre": "2022-03-14",
            "date-mod": "2022-03-14",
            }
    pri_hdu.header.update(meta)

    return pri_hdu


def get_trace_names(dir_path):
    paths = glob(dir_path + "/*.dat")
    names = [path.replace(dir_path, "").replace(".dat", "").replace("\\", "") for path in paths]

    return names


def do_main():
    dir_path = "../traces"
    trace_names = get_trace_names(dir_path)

    pri_hdu = make_pri_hdu()
    cat_hdu = make_cat_hdu(trace_names)
    trace_hdus = make_spec_trace_hdu(trace_names, dir_path)

    trace_hdulist = fits.HDUList([pri_hdu] + [cat_hdu] + trace_hdus)
    trace_hdulist.writeto("../traces/LSS_TRACES.fits", overwrite=True)


if __name__ == '__main__':
    do_main()
