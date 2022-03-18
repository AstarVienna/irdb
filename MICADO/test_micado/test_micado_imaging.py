# integration test using everything and the MICADO package
import pytest
from pytest import approx

import numpy as np

import scopesim as sim
from scopesim import rc
from scopesim.source import source_templates as st

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

PLOTS = False

TOP_PATH = "../../"
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH


class TestLimiting:
    """
    from Ric's excel doc (Signal_noise_estimator_MICADO_2018.04.03)
    [on google drive]

                                            J       H       K
    5-sigma @ 5hr EXPTIME   [Vega mags]     27.9    27.5    27.1
    sky + instr. bkg 	    [e-/pixel/s]    5.0     28.4	78.7
    sky + instr. bkg [ScopeSim]             6.5     38      60
    Photometric aperture                    3x3     5x5     5x5     # orig 2x2, 3x3, 4x4
    ScopeSim + MICADO (MCAO)                27.6    27.3    26.9

    Just out of interest:
    ScopeSim + MICADO (SCAO)                29.7    28.5    28.0

    Tolerance for assert is 0.3 mag (to high?)

    """
    @pytest.mark.parametrize(" fw1,    fw2,    r0, rics_lim_mag",
                             [("J",    "open", 1,  27.9),
                              ("open", "H",    2,  27.5),
                              ("open", "Ks",   2,  27.1)])
    def test_MCAO_IMG_4mas(self, fw1, fw2, r0, rics_lim_mag, ao_mode="MCAO"):

        n_stars, mmin, mmax = 400, 25, 30
        r1, r2 = 10, 15              # aperture radii  r0 (sig), r1-r2 (noise)
        src = st.star_field(n_stars, mmin, mmax, width=3, use_grid=True)

        cmds = sim.UserCommands(use_instrument="MICADO",
                                set_modes=[ao_mode, "IMG_4mas"])
        micado = sim.OpticalTrain(cmds)
        micado.cmds["!OBS.dit"] = 18000
        micado["filter_wheel_1"].change_filter(fw1)
        micado["filter_wheel_2"].change_filter(fw2)
        micado["detector_linearity"].include = False

        micado.observe(src)
        hdul = micado.readout()[0]

        if PLOTS:
            plt.subplot(131)
            imp = micado.image_planes[0].hdu.data       # e-/pixel/s
            plt.imshow(imp, norm=LogNorm(), vmin=np.median(imp), vmax=1.01*np.median(imp))

            plt.subplot(132)
            det = hdul[1].data
            plt.imshow(det, norm=LogNorm(), vmin=np.median(det), vmax=1.01*np.median(det))

        offset = 2      # this needs to be addressed
        xpix, ypix = src.fields[0]["x"].data, src.fields[0]["y"].data
        xpix = xpix / 0.004 + 512 + offset
        ypix = ypix / 0.004 + 512 + offset
        mags = np.round(np.linspace(mmin, mmax, n_stars), 1)

        snrs = []
        for x, y, mag in zip(xpix, ypix, mags):
            x, y = int(x+0.5), int(y+0.5)
            sig_im = np.copy(det[y-r0:y+r0+1, x-r0:x+r0+1])
            bg_im =  np.copy(det[y-r2:y+r2+1, x-r2:x+r2+1])
            bg_im[r1:-r1, r1:-r1] = 0

            bg_median = np.median(bg_im[bg_im > 0])
            bg_std = np.std(bg_im[bg_im > 0])
            # bg_std = np.sqrt(bg_median)
            noise = bg_std * np.sqrt(np.prod(sig_im.shape)) * np.sqrt(2)        # sqrt(2) comes from BG subtraction (see Rics doc)
            signal = np.sum(sig_im - bg_median)
            snr = signal/noise
            snrs += [snr]

            if PLOTS:
                plt.plot([x-r0, x+r0, x+r0, x-r0, x-r0],
                         [y-r0, y-r0, y+r0, y+r0, y-r0], "g")
                plt.plot([x-r1, x+r1, x+r1, x-r1, x-r1],
                         [y-r1, y-r1, y+r1, y+r1, y-r1], "y")
                plt.plot([x-r2, x+r2, x+r2, x-r2, x-r2],
                         [y-r2, y-r2, y+r2, y+r2, y-r2], "r")

                plt.text(x+r2, y+r2, str(round(snr, 1)), color="w")
                plt.text(x-r2, y-r2, str(mag), color="w")

        from scipy.stats import linregress
        snrs = np.array(snrs)
        results = linregress(mags[snrs > 5], np.log10(snrs[snrs > 5]))
        m, c = results[:2]
        sigma = 5
        lim_mag = (np.log10(sigma) - c) / m

        if PLOTS:
            plt.subplot(133)
            plt.plot(mags, snrs, ".", alpha=0.3)
            plt.plot(mags, 10 ** (m * mags + c), "r")

            plt.axhline(sigma)
            plt.axvline(lim_mag)
            plt.text(lim_mag, sigma, str(lim_mag),
                     horizontalalignment="left",
                     verticalalignment="bottom")

            plt.show()

        assert lim_mag == approx(rics_lim_mag, abs=0.3)
