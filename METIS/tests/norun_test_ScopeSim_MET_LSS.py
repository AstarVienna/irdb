"""
0-mag photon fluxes from Vega Spectrum
--------------------------------------
J band (J=0mag)   --> 3505e6 ph/s/m2
H band (H=0mag)   --> 2416e6 ph/s/m2
Ks band (Ks=0mag) --> 1211e6 ph/s/m2
Lp band (Lp=0mag) -->  576e6 ph/s/m2
Mp band (Mp=0mag) -->  268e6 ph/s/m2


ScopeSim using SkyCalc defaults above atmosphere
------------------------------------------------
J  BG: 688 ph/s/m2/arcsec2
H  BG: 4e3 ph/s/m2/arcsec2
Ks BG: 1e3 ph/s/m2/arcsec2
Lp BG: 4e6 ph/s/m2/arcsec2


Theoretical METIS BG based on SkyCalc
-------------------------------------
Ks BG:  30e3 ph/s/pixel
Lp BG: 118e3 ph/s/pixel
Mp BG: 3.2e6 ph/s/pixel

"""
import pytest
pytest.skip("we'll come back to this one day (hopefully)",
            allow_module_level=True)
from pytest import approx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from astropy import units as u

import scopesim as sim
from scopesim.source.source_templates import star, empty_sky
from scopesim import rc

import hmbp

rc.__currsys__['!SIM.file.local_packages_path'] = "../../"

PLOTS = False


class TestMetisLss:
    def test_works(self):
        src = star(flux=0, x=0, y=0) + \
              star(flux=2, x=-2, y=0) + \
              star(flux=4, x=2, y=0)
        # src = empty_sky()

        cmds = sim.UserCommands(use_instrument="METIS", set_modes=["lss_m"])
        cmds["!OBS.dit"] = 1
        metis = sim.OpticalTrain(cmds)
        metis["psf"].include = False

        metis.observe(src)
        hdus = metis.readout()

        implane = metis.image_planes[0].data
        det_img = hdus[0][1].data
        assert 0 < np.sum(implane) < np.sum(det_img)

        if PLOTS:
            plt.subplot(122)
            plt.imshow(hdus[0][1].data, origin="lower", norm=LogNorm(), vmin=1)
            plt.title("Detctor Plane (with noise)")
            plt.colorbar()

            plt.subplot(121)
            plt.imshow(metis.image_planes[0].data, origin="lower",
                       norm=LogNorm(), vmin=1)
            plt.title("Image Plane (noiseless)")
            plt.colorbar()
            plt.show()

    def test_integrated_spec_bg_equals_img_bg(self):
        src = empty_sky()

        toggle_effects = [
                          # "skycalc_atmosphere",
                          # "telescope_reflection",
                          # "common_fore_optics",
                          # "metis_img_lm_mirror_list",
                          # "quantum_efficiency",
                          # "psf",
                          ]

        cmds_img = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
        cmds_img["!SIM.spectral.wave_min"] = 3.5
        cmds_img["!SIM.spectral.wave_max"] = 4.0
        metis_img = sim.OpticalTrain(cmds_img)
        for eff in toggle_effects:
            metis_img[eff].include = False

        metis_img.observe(src)
        img = metis_img.image_planes[0].data

        cmds_lss = sim.UserCommands(use_instrument="METIS", set_modes=["lss_l"])
        cmds_lss["!SIM.spectral.wave_min"] = 3.5
        cmds_lss["!SIM.spectral.wave_max"] = 4.0
        metis_lss = sim.OpticalTrain(cmds_lss)
        for eff in toggle_effects:
            metis_lss[eff].include = False

        metis_lss.observe(src)
        lss = metis_lss.image_planes[0].data

        img_med = np.median(img)
        lss_med = np.median(np.sum(lss, axis=0))

        # 7x because we need to sum up the overlapping slice images
        # and the slit is 7 pixels wide
        assert 7 * img_med == approx(lss_med, rel=0.05)

    def test_integrated_vega_flux_is_what_is_expected(self):
        cmds = sim.UserCommands(use_instrument="METIS", set_modes=["lss_l"])
        metis = sim.OpticalTrain(cmds)

        toggle_effects = [
                          "skycalc_atmosphere",
                          "telescope_reflection",
                          "common_fore_optics",
                          # "metis_img_lm_mirror_list",
                          # "quantum_efficiency",
                          # "psf"
                          ]
        for eff in toggle_effects:
            metis[eff].include = False

        src = star(flux=1 * u.Jy)
        metis.observe(src)

        img = metis.image_planes[0].data
        metis_phs = img.sum()

        sys_trans = metis.optics_manager.system_transmission
        one_jy_phs = hmbp.in_one_jansky(sys_trans).value * 978

        if PLOTS:
            plt.imshow(img, origin="lower", norm=LogNorm(), vmin=1e-8)
            plt.show()

        assert metis_phs == approx(one_jy_phs, rel=0.1)

    def test_print_metis_effects(self):
        cmds = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
        metis = sim.OpticalTrain(cmds)
        print(metis.effects)
