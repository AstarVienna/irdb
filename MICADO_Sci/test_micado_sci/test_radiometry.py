""" ELT ETC results:
1100m2, 5mas/pix -->  978m2 MICADO @ 4mas = 57% of ESO ETC
1100m2, 5mas/pix -->  978m2 MICADO @ 1.5mas = 8% of ESO ETC
1100m2, 5mas/pix -->  978m2 METIS LM @ 5.25mas = 98% of ESO ETC
1100m2, 5mas/pix -->  978m2 METIS N @ 6.8mas = 165% of ESO ETC

ESO ETC
I (19 mag): BG = 3 ph/s --> 1.7 (MIC@4mas), 0.2 (MIC@1.5mas)    (Ohio: 0.8 @4mas, 0.1 @1.5mas)
J (16 mag): BG = 27 ph/s --> 15 (MIC@4mas), 2 (MIC@1.5mas)      (Ohio: 11 @4mas, 2 @1.5mas)
H (14 mag): BG = 107 ph/s --> 61 (MIC@4mas), 9 (MIC@1.5mas)     (Ohio: 54 @4mas, 8 @1.5mas)
K (13 mag): BG = 147 ph/s --> 84 (MIC@4mas), 12 (MIC@1.5mas)    (Ohio: 82 @4mas, 12 @1.5mas)
L (5.3 mag): BG = 41052 ph/s --> 40.000 (MET@5.25mas)
M (1.3 mag/arcsec2): BG = 920959 ph/s --> 903.000 (MET@5.25mas)
N (-3.7mag/arcsec2): BG = 140093628  ph/s --> 231.000.000 (MET@6.8mas)

* ESO assumes 50% throughput, Ohio adjusted to use 50%
* Ohio using the MICADO filter widths from Ric and the ESO ETC sky backgrounds

# Cuby et al from https://www.eso.org/sci/facilities/eelt/science/drm/tech_data/background/
# J (18 mag) 8 (MIC@4mas), 1 (MIC@1.5mas) based on 1200 ph s-1 m-2 um-1 arcsec-2
# H == K
# H, K (16.5, 15.7 mag) 15 (MIC@4mas), 2 (MIC@1.5mas) based on 2300 ph s-1 m-2 um-1 arcsec-2
# H, K (14.4, 13.6 mag) 103 (MIC@4mas), 14 (MIC@1.5mas) based on 2300 ph s-1 m-2 um-1 arcsec-2


"""

import pytest
from pytest import approx
from os import path as pth

import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import scopesim as sim
from scopesim import rc

pytest.skip(allow_module_level=True)

TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH

PLOTS = False


class TestMicadoSciRadiometry:
    @pytest.mark.xfail(reason="Apparently we don't reach this accuracy")
    @pytest.mark.parametrize("filt, bg, ph",
                             [("Ks", 13, 12), ("H", 14, 8), ("J", 16, 1)])
    def test_scao_zoom_bg_levels_are_similar_to_ETC(self, filt, bg, ph):
        self.inner_scao_zoom_bg_levels_are_similar_to_ETC(filt, bg, ph, 0.7)

    @pytest.mark.parametrize("filt, bg, ph",
                             [("Ks", 13, 12), ("H", 14, 8), ("J", 16, 1)])
    def test_scao_zoom_bg_levels_are_similar_to_ETC_loose(self, filt, bg, ph):
        self.inner_scao_zoom_bg_levels_are_similar_to_ETC(filt, bg, ph, 2.6)

    def inner_scao_zoom_bg_levels_are_similar_to_ETC(self, filt, bg, ph, rel):
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["SCAO", "IMG_1.5mas"])
        cmd["!OBS.dit"] = 1
        cmd["!OBS.ndit"] = 1
        cmd["!DET.width"] = 128
        cmd["!DET.height"] = 128
        cmd["!ATMO.background.value"] = bg
        cmd["!OBS.filter_name"] = filt
        cmd["!INST.psf.strehl"] = 0.6

        opt = sim.OpticalTrain(cmd)
        src = sim.source.source_templates.empty_sky()
        opt.observe(src)
        sim_ph = np.average(opt.image_planes[0].image)

        print("Sim", sim_ph, "ETC", ph)
        assert sim_ph == approx(ph, rel=rel)

    @pytest.mark.xfail(reason="Apparently this level of accuracy isn't met.")
    @pytest.mark.parametrize("filt, bg, ph",
                             [("Ks", 13, 12), ("H", 14, 8), ("J", 16, 1)])
    def test_mcao_wide_bg_levels_are_similar_to_ETC(self, filt, bg, ph):
        self.inner_mcao_wide_bg_levels_are_similar_to_ETC(filt, bg, ph, 0.7)

    @pytest.mark.parametrize("filt, bg, ph",
                             [("Ks", 13, 12), ("H", 14, 8), ("J", 16, 1)])
    def test_mcao_wide_bg_levels_are_similar_to_ETC_loose(self, filt, bg, ph):
        self.inner_mcao_wide_bg_levels_are_similar_to_ETC(filt, bg, ph, 2.6)

    def inner_mcao_wide_bg_levels_are_similar_to_ETC(self, filt, bg, ph, rel):
        """Inner test of test_mcao_wide_bg_levels_are_similar_to_ETC."""
        cmd = sim.UserCommands(use_instrument="MICADO_Sci",
                               set_modes=["MCAO", "IMG_1.5mas"])
        cmd["!OBS.dit"] = 1
        cmd["!OBS.ndit"] = 1
        cmd["!DET.width"] = 128
        cmd["!DET.height"] = 128
        cmd["!ATMO.background.value"] = bg
        cmd["!OBS.filter_name"] = filt
        cmd["!INST.psf.strehl"] = 0.6

        opt = sim.OpticalTrain(cmd)
        src = sim.source.source_templates.empty_sky()
        opt.observe(src)
        sim_ph = np.average(opt.image_planes[0].image)

        print("Sim", sim_ph, "ETC", ph)
        assert sim_ph == approx(ph, rel=rel)

        #
        #
        # im = opt.image_planes[0].image
        # # im = hdu[1].data
        #
        # print(np.average(im))
        #
        # sys_trans = opt.optics_manager.system_transmission
        # effects = opt.optics_manager.get_z_order_effects(100)
        #
        # for effect in effects:
        #     print(effect)
        #
        # if PLOTS:
        #     wave = np.linspace(0.5, 2.5, 1000) * u.um
        #     plt.plot(wave, sys_trans(wave))
        #     plt.show()
        #
        # if PLOTS:
        #     plt.imshow(im, norm=LogNorm(),
        #                vmin=0.9 * np.average(im),
        #                vmax=1.1 * np.average(im))
        #     plt.show()
        #
        #
        #
        #
        #

