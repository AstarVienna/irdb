import pytest

from matplotlib import pyplot as plt
from astropy.io import fits, ascii
from astropy.table import Table


class TestSpecTraceVsDetectors:
    def plot_detectors(self):
        tbl = ascii.read("../FPA_array_layout.dat")
        print(tbl)

        plt.figure(figsize=(7, 7))
        for row in tbl:
            x, y = row["x_cen"], row["y_cen"]
            dx, dy =  row["xhw"], row["yhw"]
            plt.plot([x-dx, x+dx, x+dx, x-dx, x-dx],
                     [y-dy, y-dy, y+dy, y+dy, y-dy], c="b")
            plt.text(x, y, row["id"],
                     horizontalalignment="center", verticalalignment="center", fontsize=18)

        for ext in range(2, 3):
            tbl = Table(fits.getdata("../TRACE_MICADO.fits", ext=ext))
            plt.scatter(tbl["x"], tbl["y"], c=tbl["wavelength"], s=10, cmap="hot_r")

            plt.text(tbl["x"][3], tbl["y"][3], f'{round(tbl["wavelength"][3], 2)} um',
                     horizontalalignment="center", verticalalignment="center", fontsize=14)
            plt.text(tbl["x"][-2], tbl["y"][-2], f'{round(tbl["wavelength"][-2], 2)} um',
                     horizontalalignment="center", verticalalignment="center", fontsize=14)

        plt.arrow(0, 5, 0, 20, width=1, fc="k")
        plt.arrow(5, 0, 20, 0, width=1, fc="k")

        plt.xlabel("X distance from optical axis [mm]")
        plt.ylabel("Y distance from optical axis [mm]")
        plt.title("SimCADO detector layout (May 2021)\nLooking through the bottom of the detector towards the sky")

        plt.show()

    @pytest.mark.parametrize("name, wave_min, wave_max, xi_min, xi_max",
                             [#('IzJ-band 3 arcsec', 0.83, 1.57, -1.6, 1.6),
                              # ('J-band 15 arcsec', 1.16, 1.35, -6, 11),
                              ('HK-band 15 arcsec', 1.5, 2.45, -6, 11)
                              ])
    def plot_trace_file(self, name, wave_min, wave_max, xi_min, xi_max):

        plt.figure(figsize=(20, 15))

        tbl = ascii.read("../FPA_array_layout.dat")
        det_xs, det_ys = [], []
        for row in tbl:
            x, y = row["x_cen"], row["y_cen"]
            dx, dy = row["xhw"], row["yhw"]
            det_xs += [[x - dx, x + dx, x + dx, x - dx, x - dx]]
            det_ys += [[y - dy, y - dy, y + dy, y + dy, y - dy]]

        with fits.open("../TRACE_MICADO.fits") as hdul:
            for i, hdu in enumerate(hdul[2:]):
                tbl = Table(hdu.data)
                mask = (tbl["wavelength"] >= wave_min) * \
                       (tbl["wavelength"] <= wave_max) * \
                       (tbl["xi"] >= xi_min) * \
                       (tbl["xi"] <= xi_max)
                x, y = tbl["x"][mask], tbl["y"][mask]
                xi_colour = tbl["xi"][mask]

                plt.subplot(3, 5, i+1)
                plt.plot(x, y, "r-", alpha=0.4)
                plt.scatter(x, y, c=xi_colour, s=10)

                for det_x, det_y in zip(det_xs, det_ys):
                    plt.plot(det_x, det_y, c="b", alpha=0.3)

                plt.title(hdu.header["EXTNAME"])
                plt.gca().set_aspect('equal', 'box')
                plt.xlim(-120, 120)
                plt.ylim(-120, 120)

        plt.suptitle(f"{name}\nWavelengths: [{wave_min}, {wave_max}], "
                     f"xi: [{xi_min}, {xi_max}]")
        fname = f"new_spec_traces_{name}_lam_{wave_min}_{wave_max}_xi_{xi_min}_{xi_max}"
        # plt.savefig(fname + ".png", format="png")
        # plt.savefig(fname + ".pdf", format="pdf")
        # plt.show()

    @pytest.mark.parametrize("name, wave_min, wave_max, xi_min, xi_max",
                             [('IzJ-band 3 arcsec', 0.83, 1.57, -1.6, 1.6),
                              ('J-band 15 arcsec', 1.16, 1.35, -6, 11),
                              ('HK-band 15 arcsec', 1.5, 2.45, -6, 11)
                              ])
    def plot_trace_file_vertical(self, name, wave_min, wave_max, xi_min, xi_max):

        plt.figure(figsize=(20, 15))

        tbl = ascii.read("../FPA_array_layout.dat")
        det_xs, det_ys = [], []
        for row in tbl:
            x, y = row["x_cen"], row["y_cen"]
            dx, dy = row["xhw"], row["yhw"]
            det_xs += [[x - dx, x + dx, x + dx, x - dx, x - dx]]
            det_ys += [[y - dy, y - dy, y + dy, y + dy, y - dy]]

        with fits.open("../TRACE_MICADO.fits") as hdul:
            for i, hdu in enumerate(hdul[2:]):
                for xi, c in zip([-5, -1.5, 0, 1.5, 10], "mbgyr"):
                    tbl = Table(hdu.data)
                    mask = (tbl["wavelength"] >= wave_min) * \
                           (tbl["wavelength"] <= wave_max) * \
                           (tbl["xi"] >= xi-0.1) * \
                           (tbl["xi"] <= xi+0.1)
                    x, y = tbl["x"][mask], tbl["y"][mask]
                    # xi_colour = tbl["xi"][mask]

                    plt.subplot(3, 5, i+1)
                    plt.plot(x, y, c+"-", alpha=0.4)
                    plt.scatter(x, y, c=c, s=10)

                for det_x, det_y in zip(det_xs, det_ys):
                    plt.plot(det_x, det_y, c="b", alpha=0.3)

                plt.title(hdu.header["EXTNAME"])
                plt.gca().set_aspect('equal', 'box')
                plt.xlim(-120, 120)
                plt.ylim(-120, 120)

        plt.suptitle(f"{name}\nWavelengths: [{wave_min}, {wave_max}], "
                     f"xi: [{xi_min}, {xi_max}]")
        fname = f"new_spec_traces_{name}_lam_{wave_min}_{wave_max}_xi_{xi_min}_{xi_max}"
        # plt.savefig(fname + ".png", format="png")
        # plt.savefig(fname + ".pdf", format="pdf")
        # plt.show()
