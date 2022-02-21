from matplotlib import pyplot as plt
from astropy.io import fits, ascii
from astropy.table import Table


class TestSpecTraceVsDetectors:
    def test_plot_detectors(self):
        tbl = ascii.read("../FPA_array_layout.dat")
        print(tbl)

        plt.figure(figsize=(7, 7))
        for row in tbl:
            x, y = row["x_cen"], row["y_cen"]
            dx, dy =  row["xhw"], row["yhw"]
            plt.plot([x-dx, x+dx, x+dx, x-dx, x-dx],
                     [y-dy, y-dy, y+dy, y+dy, y-dy], c="b")
            plt.text(x, y, row["id"], horizontalalignment="center", verticalalignment="center", fontsize=18)

        for ext in range(2, 3):
            tbl = Table(fits.getdata("../TRACE_MICADO.fits", ext=ext))
            plt.scatter(tbl["x"], tbl["y"], c=tbl["wavelength"], s=10, cmap="hot_r")

            plt.text(tbl["x"][3], tbl["y"][3], f'{round(tbl["wavelength"][3], 2)} um', horizontalalignment="center", verticalalignment="center", fontsize=14)
            plt.text(tbl["x"][-2], tbl["y"][-2], f'{round(tbl["wavelength"][-2], 2)} um', horizontalalignment="center", verticalalignment="center", fontsize=14)


        plt.arrow(0, 5, 0, 20, width=1, fc="k")
        plt.arrow(5, 0, 20, 0, width=1, fc="k")

        plt.xlabel("X distance from optical axis [mm]")
        plt.ylabel("Y distance from optical axis [mm]")
        plt.title("SimCADO detector layout (May 2021)\nLooking through the bottom of the detector towards the sky")

        plt.show()
