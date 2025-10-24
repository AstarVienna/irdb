"""Add an extension with coefficients for the predisperser

Taken from Fig.3-15 of E-REP-ATC-MET-1003_3-0
"""
from astropy.io import fits
from astropy.table import Table
TRACEFILE = "TRACE_LMS.fits"


def add_predisperser():
    # Coefficients in ascending order of powers of wavelength
    coeff = fits.Column(name="coefficients", format="E",
                        array=[-6.0585, 9.1657, -2.7017, 0.3825, -0.0205])
    power = fits.Column(name="power", format="I",
                        array=[0, 1, 2, 3, 4])
    hdu = fits.BinTableHDU.from_columns([power, coeff])

    hdu.header["EXTNAME"] = "Predisperser"

    with fits.open(TRACEFILE) as hdul:
        # Append the new HDU
        hdul.append(hdu)

        # Update the catalogue
        cat = hdul["CATALOGUE"]
        tab = Table(cat.data)
        tab.add_row(('Predisperser', 5, 0, 0))
        nhdu = fits.BinTableHDU(tab)
        nhdu.header["EXTNAME"] = "CATALOGUE"
        hdul[1] = nhdu

        # Update the primary header
        hdul[0].header.update(dict(
            DATE="2025-10-06",
            SOURCE="E-REP-ATC-MET-1003_3-0, E-REP-ATC-MET-1016_1-0",
            DATE_MOD="2025-10-06",
            HISTORY="2025-10-06 (OC) append predisperser angle fit"))
        hdul.writeto("test_trace.fits", overwrite=True)
        print("Output written to test_trace.fits. Rename to", TRACEFILE," when checked for correctness.")



if __name__ == "__main__":
    add_predisperser()
