from glob import glob
from os import path as pth
from astropy.io import fits, ascii
from astropy.table import Table

files = glob("wfc3_ir_f*_mjd_*_syn.fits")
output_format = "../TER_filter_{}.dat"

for fname in files:
    data = fits.getdata(fname)
    tbl = Table(data)
    tbl.columns[0].name = "wavelength"
    tbl.columns[1].name = "transmission"
    new_table = Table()
    new_table.add_columns([tbl["wavelength"], tbl["transmission"]])
    cmts = ["author: Kieran Leschinski",
            "source: https://stsynphot.readthedocs.io/en/latest/stsynphot/data_hst.html",
            "description: WFC3 IR Filter Curve",
            "date_created: 2019-11-19",
            "date_modified: 2019-11-19",
            "status: measured",
            "orig_filename: {}".format(fname),
            "wavelength_unit: Angstrom"]
    new_table.meta["comments"] = cmts
    new_table.write(output_format.format(fname[8:13].upper()),
                    format="ascii.fixed_width", overwrite=True, delimiter=None)
