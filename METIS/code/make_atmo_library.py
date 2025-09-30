"""Create a TERCurve library

Use the script with a parameter:
* make_atmo_library.py make
  Creates a multiextension fits file "Leiden_atmo_ter.fits" with
  - 0: PDU
  - 1: Catalogue Table of contents with PWV and corresponding extension
  - 2: WAVELENGTH Common wavelength vector for all spectra
  - 3..: Extensions for PWV between 1 and 50
* make_atmo_library.py plot
  Plots a selection of the spectra from "Leiden_atmo_ter.fits".
"""
import sys
import numpy as np
from matplotlib import pyplot as plt
from astropy.io import fits
from astropy.table import Table

OUTFILE = "Leiden_atmo_ter.fits"

def make_mef_fits(pwvs):
    """Arrange TERcurve for varying pwv values in many BinTableHDUs"""
    # extension 1: table of contents
    toc = Table(names=("extension_id", "pwv", "extension_name"),
                dtype=("i2", "f2", "S8"))

    extid = 1
    toc.add_row([extid, -999, "Catalogue"])

    reffile = "leiden_spectra/LBL_A10_w0100_R0120000_ALL_Leiden_LM_R.fits"

    # extension 2: table of wavelengths
    extid += 1
    hdulist = [0, 0]    # contains wavehdu and pwvhdus, but not toc
    wavelengths = fits.getdata(reffile)['lam']
    wavecol = fits.Column(name="wavelength", array=wavelengths,
                          format="E", unit="um")
    wavehdu = fits.BinTableHDU.from_columns([wavecol])
    wavehdu.header["EXTNAME"] = "WAVELENGTH"
    hdulist.append(wavehdu)
    toc.add_row([extid, -999, "WAVELENGTH"])

    # extension 3+: ter curves
    extid += 1
    for p in pwvs:
        transfile = f"leiden_spectra/LBL_A10_w{int(100*p):04d}_R0120000_ALL_Leiden_LM_T.fits"
        transdata = fits.getdata(transfile)
        transcol = fits.Column(name="transmission", array=transdata['flux'],
                               format="E")

        emissfile = f"leiden_spectra/LBL_A10_w{int(100*p):04d}_R0120000_ALL_Leiden_LM_R.fits"
        emissdata = fits.getdata(emissfile)
        emisscol = fits.Column(name="emission", array=emissdata['flux'],
                               format="E", unit="ph s-1 m-2 um-1 arcsec-2")

        pwvhdu = fits.BinTableHDU.from_columns([transcol, emisscol])
        extname = f"PWV_{int(p):02d}"
        pwvhdu.header['EXTNAME'] = extname
        pwvhdu.header['PWV'] = (p, "Precipitable Water Vapour [mm]")
        pwvhdu.header['EMITFILE'] = emissfile[15:]
        pwvhdu.header['TRNSFILE'] = transfile[15:]
        hdulist.append(pwvhdu)
        toc.add_row([extid, p, extname])
        extid += 1

    tochdu = fits.BinTableHDU(toc)
    tochdu.header['EXTNAME'] = "Catalogue"
    hdulist[1] = tochdu


    phdu = fits.PrimaryHDU()    # Fill with stuff

    phdu.header["ECAT"] = 1
    phdu.header["EDATA"] = 3

    meta = {
        "author": "Oliver Czoske",
        "source": "Wolfgang Kausch",
        "descript": "Leiden sky emission and transmission",
        "date-cre": "2025-09-30",
        "date-mod": "2025-09-30",
        "status": "Finished for AIT"
    }
    phdu.header.update(meta)

    refheader = fits.getheader(reffile, ext=0)
    _ = refheader.pop("PWV")
    phdu.header.update(refheader)

    hdulist[0] = phdu
    hdulist = fits.HDUList(hdulist)
    hdulist.writeto(OUTFILE, overwrite=True)

def plot_leiden_sky(filename=OUTFILE):
    """Plot a selection of the Leiden sky spectra

    The spectra are in Leiden_atmo_ter.fits.
    The plot shows transmission and emission spectra
    for PWV = 10, 20, 30, 40, and 50 between 4.95 and 5 um.
    """
    _, ax = plt.subplots(2, 1, sharex=True)
    ax[0].set_title("Transmission")
    ax[1].set_title("Radiance")

    with fits.open(filename) as hdul:
        lam = hdul[2].data['wavelength']
        ax[1].set_xlabel("Wavelength [um]")
        ax[1].set_ylabel(hdul[3].header['TUNIT2'])
        for hdu in hdul[12::10]:
            print(hdu.header['PWV'])
            ax[0].plot(lam, hdu.data['transmission'], lw=0.5, label=hdu.header['PWV'])
            ax[1].plot(lam, hdu.data['emission'], lw=0.5, label=hdu.header['PWV'])
    plt.xlim(4.9, 5)
    ax[1].legend()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("""Usage:
        python make_atmo_library.py <make|plot>""")
        sys.exit()

    if sys.argv[1] == "make":
        pwvlist = np.arange(1, 51, dtype=np.float32)
        make_mef_fits(pwvlist)
    elif sys.argv[1] == "plot":
        plot_leiden_sky()
