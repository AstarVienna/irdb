"""Conversion of MPIA provided filter curves to irdb format

Input: two excel files
       - E-LIS-MPIA-MET-1208_1-0_IMG_LM_science-filter_transmission_data.xlsx
       - E-LIS-MPIA-MET-1208_1-0_IMG_N_science-filter_transmission_data.xlsx
       with one sheet per filter. Each sheet has a table with two columns:
            - "nm": Wavelength in nanometers
            - "transmission"
Output: One ascii file per filter, with a two-column table ("wavelength",
        "transmission"), where wavelength is in um (original value divided
        by 1000), and a yaml header.
The variable `PLOT` turns on a plot method that shows the new and old filter
curves (only works when the latter are available!)

Author: Oliver Czoske , 2025-02-12, adapted 2025-06-18
"""
import textwrap
from matplotlib import pyplot as plt

import pandas as pd

from astropy.io import ascii as ioascii

def plot_curves(wb, new, old, plottitle):
    """Plot the old and new filter curves"""
    nrow = (len(new) + 2) // 3
    fig, axes = plt.subplots(nrow, 3, sharex=True, sharey=True, figsize=(8, 11.2),
                             layout="constrained")

    for i, key in enumerate(new.keys()):
        ax = axes.flatten()[i]
        d_new = pd.read_excel(wb, new[key])
        d_old = ioascii.read(old[key])
        ax.plot(d_new['nm']/1000, d_new['transmission'], label="new")
        ax.plot(d_old['wavelength'], d_old['transmission'], label="old")
        ax.set_title(key)
        if i == 0:
            ax.legend()
    fig.supxlabel(r"Wavelength [$\mu$m]")
    plt.savefig(plottitle)
    plt.show()

def convert_curves(wb, new):
    """Convert xlsx to ascii format"""
    for key, sheet in new.items():
        d_new = pd.read_excel(wb, sheet)
        d_new = d_new.rename(columns={"nm": "wavelength"})
        d_new['wavelength'] /= 1000
        outfile = f"new_filters/TC_filter_{key}.dat"

        with open(outfile, 'w', encoding="utf-8") as fd:
            fd.write(textwrap.dedent(f"""\
            # author : Oliver Czoske
            # source : E-LIS-MPIA-MET-1208_1-0
            # date_created : 2025-06-18
            # date_modified : 2025-06-18
            # status : Measurement
            # type : filter:transmission
            # wavelength_unit : um
            # center : {float(sheet[:5].replace(",", ".")):.3f}
            # comment : {key} filter, built by Materion, procured by MPIA
            # changes :
            #
            """))
            fd.write("wavelength  transmission\n")
            for w, t in d_new.values:
                fd.write(f"{w:.5f}       {t:.18f}\n")


def do_lm(plot=False):
    """Plots and converts LM filter curves"""

    lm_new = {'H2O-ice': '3,100um-H2O-ice',
              'PAH_3.3': '3,300um-PAH-3.3',
              'short-L': '3,300um-short-L',
              'PAH_3.3_ref': '3,445um-PAH-3.3-ref',
              'L_spec': '3,525um-full-L',
              'HCI_L_short': '3,600um-HCI-L-short',
              'Lp': '3,800um-L´',
              'Br_alpha_ref':'3,945um-Br-alpha-ref',
              'HCI_L_long': '3.825um-HCI-L-long',
              'Br_alpha': '4,050um-Br-alpha',
              'IB_4.05': '4,050um-IB4.05',
              'CO_1-0_ice': '4,650um-COice',
              'Mp': '4,775um-M´',
              'M_spec': '4,850um-full-M',
              'CO_ref': '4,950um-CO-ref'}

    lm_old = {k: f"filters/TC_filter_{k}.dat" for k in lm_new}
    lm_wb = pd.ExcelFile("E-LIS-MPIA-MET-1208_1-0_IMG_LM_science-filter_transmission_data.xlsx")
    if plot:
        plot_curves(lm_wb, lm_new, lm_old, "LM_filter_curves_compared.pdf")
    convert_curves(lm_wb, lm_new)
    lm_wb.close()


def do_n(plot=False):
    """Plot and convert N filter curves"""

    n_new = {
        'PAH_8.6': '8,600um-PAH-8.6',
        'N1': '8,650um-N1',
        'PAH_8.6_ref': '9,100um-PAH-8.6-ref',
        'N_spec': '10,500um-full-N',
        'S_IV': '10,500um-S-IV',
        'S_IV_ref': '10,795um-S-IV-ref',
        'PAH_11.25': '11,200um-PAH-11.25',
        'PAH_11.25_ref': '11,650um-PAH-11.25-ref',
        'N2': '11,275um-N2',
        'N3': '12,300um-N3',
        'Ne_II': '12,820um-NeII',
        'Ne_II_ref': '13,120um-NeII-ref'}

    n_old = {k: f"filters/TC_filter_{k}.dat" for k in n_new}
    n_wb = pd.ExcelFile("E-LIS-MPIA-MET-1208_1-0_IMG_N_science-filter_transmission_data.xlsx")

    if plot:
        plot_curves(n_wb, n_new, n_old, "N_filter_curves_compared.pdf")
    convert_curves(n_wb, n_new)
    n_wb.close()


if __name__ == "__main__":
    PLOT = False
    print("-------------- Doing LM ----------------")
    do_lm(plot=PLOT)
    print("-------------- Doing N ----------------")
    do_n(plot=PLOT)
