# -*- coding: utf-8 -*-
"""
Tests the MCAO limiting magnitudes against the values from from Ric's excel doc
[Signal_noise_estimator_MICADO_2018.04.03]

Comments
--------
- 2022-03-18 (KL) Green locally
  ScopeSim limiting mags are 0.3 mag lower in J, 0.2 mags lower H,Ks
  The differing BG levels may cause this

"""

import os
from pathlib import Path
import pytest
from pytest import approx

import numpy as np
from scipy.stats import linregress
import matplotlib as mpl
from matplotlib import pyplot as plt

import scopesim as sim
from scopesim import rc
from scopesim.source import source_templates as st


PATH_HERE = Path(__file__).parent
PATH_IRDB = PATH_HERE.parent.parent

rc.__config__["!SIM.file.local_packages_path"] = str(PATH_IRDB)
PLOTS = os.environ.get("READTHEDOCS", False)  # Run plots on RTD
if PLOTS:
    mpl.style.use("seaborn-v0_8")


@pytest.mark.validation
class TestLimiting:
    """
    from Ric's excel doc (Signal_noise_estimator_MICADO_2018.04.03)
    [on google drive]

    +--------------------------+----------+------+------+------+
    |                          | Units    |    J |    H |    K |
    +==========================+==========+======+======+======+
    | 5-sigma @ 5hr EXPTIME    | Vega mag | 27.9 | 27.5 | 27.1 |
    +--------------------------+----------+------+------+------+
    | sky & instr. bkg         | e-/pix/s |  5.0 | 28.4 | 78.7 |
    +--------------------------+----------+------+------+------+
    | sky & instr. bkg         | ScopeSim |  6.5 | 38   | 60   |
    +--------------------------+----------+------+------+------+
    | Photometric aperture     |          |  3x3 |  5x5 |  5x5 |
    +--------------------------+----------+------+------+------+
    | Original phot. aperture  |          |  2x2 |  3x3 |  4x4 |
    +--------------------------+----------+------+------+------+
    | ScopeSim & MICADO (MCAO) |          | 27.6 | 27.3 | 26.9 |
    +--------------------------+----------+------+------+------+
    | Just out of interest:    |          |      |      |      |
    |                          |          |      |      |      |
    | ScopeSim & MICADO (SCAO) |          | 29.7 | 28.5 | 28.0 |
    +--------------------------+----------+------+------+------+

    .. todo:: Update ScopeSim values in this table!

    Tolerance for assert is 0.3 mag (to high?)

    """

    @pytest.mark.parametrize("img_mode", ["IMG_4mas"])
    @pytest.mark.parametrize("ao_mode", ["MCAO", "SCAO"])
    @pytest.mark.parametrize(
        ("fw1", "fw2", "r0", "rics_lim_mag", "abslim"), [
            pytest.param(
                "J", "open", 1, 27.9, 1.0,
                marks=pytest.mark.xfail(
                    reason="most likely PSF contamination of nearby sources"
                ),
            ),
            pytest.param(
                "open", "H", 2, 27.5, 0.6,
                marks=pytest.mark.xfail(
                    reason="most likely PSF contamination of nearby sources"
                ),
            ),
            pytest.param(
                "open", "Ks", 2, 27.1, 0.3,
                marks=pytest.mark.xfail(
                    reason="most likely PSF contamination of nearby sources"
                ),
            ),
        ],
    )
    def test_MCAO_IMG_4mas(
        self, record_property, fw1, fw2, r0, rics_lim_mag, abslim, ao_mode, img_mode,
    ):
        filt = fw1 if fw1 != "open" else fw2
        record_property("filter", filt)
        record_property("ao_mode", ao_mode)
        record_property("img_mode", img_mode)
        record_property("expected", rics_lim_mag)
        record_property("tolerance", abslim)

        n_stars, mmin, mmax = 400, 25, 30
        r1, r2 = 10, 15  # aperture radii  r0 (sig), r1-r2 (noise)
        src = st.star_field(n_stars, mmin, mmax, width=3, use_grid=True)

        cmds = sim.UserCommands(
            use_instrument="MICADO", set_modes=[ao_mode, img_mode]
        )
        micado = sim.OpticalTrain(cmds)
        micado.cmds["!OBS.dit"] = 18000  # 5 h
        micado["filter_wheel_1"].change_filter(fw1)
        micado["filter_wheel_2"].change_filter(fw2)
        micado["detector_linearity"].include = False

        micado.observe(src)
        det = micado.readout()[0][1].data
        imp = micado.image_planes[0].hdu.data  # e-/pixel/s

        if PLOTS:
            fig, (img_ax, det_ax, snr_ax) = plt.subplots(1, 3, figsize=(20, 8), layout="constrained")
            fig.suptitle(f"MICADO {ao_mode} {img_mode} {filt}-band")

            img_ax.imshow(
                imp,
                norm="log",
                vmin=np.median(imp),
                vmax=np.quantile(imp, .995),
                origin="lower",
                cmap="inferno",
            )
            img_ax.set_title("Image Plane")
            img_ax.grid(False, which="both")
            img_ax.set_xlabel("pixel")
            img_ax.set_ylabel("pixel")
            det_ax.imshow(
                det,
                norm="log",
                vmin=np.median(det),
                vmax=np.quantile(det, .998),
                origin="lower",
                cmap="inferno",
            )
            det_ax.set_title("Detector")
            det_ax.grid(False, which="both")
            det_ax.set_xlabel("pixel")
            det_ax.set_ylabel("pixel")

        midpoint_x = micado.cmds["!DET.width"] // 2
        midpoint_y = micado.cmds["!DET.height"] // 2

        xpix, ypix = src.fields[0].field["x"].data, src.fields[0].field["y"].data
        xpix = (xpix / micado.cmds["!INST.pixel_scale"] + midpoint_x).round(2)
        ypix = (ypix / micado.cmds["!INST.pixel_scale"] + midpoint_y).round(2)

        # For some bizzare reason, this is the only way the apertures end up in
        # the correct position??
        xpix = np.where(
            xpix < midpoint_x,
            np.floor(xpix),
            np.ceil(xpix)
        ).astype(int)
        ypix = np.where(
            ypix < midpoint_y,
            np.floor(ypix),
            np.ceil(ypix)
        ).astype(int)

        mags = np.round(np.linspace(mmin, mmax, n_stars), 1)
        snrs = np.array(list(self._photometry(xpix, ypix, mags, r0, r1, r2, det)))

        snr_limit = 5
        lin_fit = linregress(mags[snrs > snr_limit], np.log10(snrs[snrs > snr_limit]))
        lim_mag = (np.log10(snr_limit) - lin_fit.intercept) / lin_fit.slope

        if PLOTS:
            snr_ax.plot(mags, snrs, ".", alpha=0.5, label="Measurements")
            snr_ax.plot(mags, 10 ** (lin_fit.slope * mags + lin_fit.intercept), label="Fit")

            snr_ax.axhline(snr_limit, linestyle=":", color="#64B5CD", alpha=.7, label=f"S/N={snr_limit} limit")
            snr_ax.axvline(lim_mag, linestyle="--", color="#C44E52", alpha=.7, label=f"Limiting Mag.e @ S/N={snr_limit}")
            snr_ax.axvline(rics_lim_mag, color="#CCB974", alpha=.8, zorder=-1, label=f"Expected value\n{rics_lim_mag} +/- {abslim} mag")
            snr_ax.axvspan(rics_lim_mag - abslim, rics_lim_mag + abslim, color="#CCB974", alpha=.2)
            snr_ax.text(
                lim_mag + .1,
                snr_limit + .5,
                f"{lim_mag:.2f}",
                horizontalalignment="left",
                verticalalignment="bottom",
                fontsize=16,
                color="#C44E52",
            )
            snr_ax.set_xlabel("mag")
            snr_ax.set_ylabel("S/N")
            snr_ax.legend()
            snr_ax.set_title(f"S/N for MICADO {ao_mode} {img_mode}")

            fig_path = PATH_IRDB / f"docs/source/_static/plots/MICADO/limmag/{ao_mode}_{img_mode}_{filt}.pdf"
            fig_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(fig_path)
            record_property("link", str(fig_path.relative_to(PATH_IRDB / "docs/source")))

            plt.show()

        print(f"expected: {rics_lim_mag:.2f}, obtained: {lim_mag:.2f}, delta: {lim_mag-rics_lim_mag:.3f}")
        record_property("obtained", round(lim_mag, 2))
        record_property("difference", round(lim_mag-rics_lim_mag, 3))

        lim_mag = round(lim_mag, 4)  # for nicer output msg
        assert lim_mag == approx(rics_lim_mag, abs=abslim)

    @staticmethod
    def _photometry(xpix, ypix, mags, r0, r1, r2, det):
        for x, y, mag in zip(xpix, ypix, mags):
            sig_im = np.copy(det[y-r0:y+r0+1, x-r0:x+r0+1])
            bkg_im = np.copy(det[y-r2:y+r2+1, x-r2:x+r2+1])
            bkg_im[r1:-r1, r1:-r1] = 0  # use masked array?

            bg_median = np.median(bkg_im[bkg_im > 0])
            bg_std = np.std(bkg_im[bkg_im > 0])
            # bg_std = np.sqrt(bg_median)
            noise = bg_std * np.sqrt(np.prod(sig_im.shape)) * np.sqrt(2)  # sqrt(2) comes from BG subtraction (see Rics doc)
            signal = np.sum(sig_im - bg_median)
            snr = signal / noise

            if PLOTS:
                # Can't pass det_ax as an argument if it doesn't always exits.
                # Whatever, this works...
                _, det_ax, _ = plt.gcf().get_axes()
                det_ax.plot([x-r0, x+r0, x+r0, x-r0, x-r0],
                            [y-r0, y-r0, y+r0, y+r0, y-r0], "g")
                det_ax.plot([x-r1, x+r1, x+r1, x-r1, x-r1],
                            [y-r1, y-r1, y+r1, y+r1, y-r1], "y")
                det_ax.plot([x-r2, x+r2, x+r2, x-r2, x-r2],
                            [y-r2, y-r2, y+r2, y+r2, y-r2], "r")

                det_ax.text(x+r2, y+r2, f"{snr:.1f}", color="w")
                det_ax.text(x-r2, y-r2, f"{mag:.1f}", color="w")

            yield snr
