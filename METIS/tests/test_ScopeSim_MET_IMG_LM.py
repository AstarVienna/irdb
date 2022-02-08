"""
To do
-----
Sky background fluxes don't match with Roy's flux document
- test_sky_phs_with_full_system_transmission

Work out whether the flux components are realistic
- TestSourceFlux

"""
import pytest
from pytest import approx
import numpy as np
from scipy.misc import face

from astropy import units as u
from astropy.table import Table
from astropy.io import fits
from photutils import CircularAperture, aperture_photometry
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

import skycalc_ipy
import hmbp
import scopesim as sim
from scopesim.effects import FilterCurve
from scopesim.source.source_templates import star, empty_sky, star_field

# Set the path to the local irdb.
from scopesim import rc
rc.__currsys__['!SIM.file.local_packages_path'] = \
    "../../"

PLOTS = False


class TestRunsStartToFinish:
    def test_basic_run_makes_image(self):
        src = star(flux=0)
        src = star_field(100, 0, 20, 10, use_grid=True)
        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
        metis = sim.OpticalTrain(cmd)
        metis['detector_linearity'].include = False
        # metis['metis_psf_img'].include = False

        metis.observe(src)
        img = metis.image_planes[0].data
        hdus = metis.readout()
        img = hdus[0][1].data

        assert np.median(img) > 0

        if not PLOTS:
            plt.imshow(img, norm=LogNorm())
            plt.show()


class TestImgLMBackgroundLevels:
    @pytest.mark.parametrize("filter_name, expected_phs",
                             [("Lp", 100e3), ("Mp", 1500e3)])
    def test_how_many_bg_photons_in_METIS(self, filter_name, expected_phs):
        eff = FilterCurve(filename=f"../filters/TC_filter_{filter_name}.dat")
        phs = hmbp.in_skycalc_background(eff.throughput)     # ph/s/m2/[arcsec2]
        phs *= 978 * u.m**2 * 0.00547**2 * 0.5

        assert phs.value == approx(expected_phs, rel=0.03)

    @pytest.mark.parametrize("filter_name, expected_phs",
                             [("Lp", 100e3), ("Mp", 1500e3)])
    def test_sky_phs_with_full_system_transmission(self, filter_name, expected_phs):
        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
        cmd["!OBS.filter_name"] = filter_name
        cmd["!AMTO.pwv"] = 1.0
        cmd["!AMTO.airmass"] = 1.0
        cmd["!AMTO.temperature"] = 258

        metis = sim.OpticalTrain(cmd)
        metis['detector_linearity'].include = False
        sys_trans = metis.optics_manager.system_transmission

        phs = hmbp.in_skycalc_background(sys_trans)  # ph/s/m2/[arcsec2]
        phs *= metis.cmds["!TEL.area"] * u.m**2 * \
               metis.cmds["!INST.pixel_scale"] ** 2

        assert phs.value == approx(expected_phs, rel=0.1)   # ph/s/pixel

    @pytest.mark.parametrize("filter_name, expected_phs",
                             [("Lp", 100e3), ("Mp", 1300e3)])
    def test_background_level_is_around_roys_level(self, filter_name, expected_phs):
        src = empty_sky()
        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
        cmd["!OBS.filter_name"] = filter_name
        metis = sim.OpticalTrain(cmd)
        metis['detector_linearity'].include = False

        metis.observe(src)
        img = metis.image_planes[0].data

        assert np.median(img) == approx(expected_phs, rel=0.1)

    def test_instrument_throughput_level_is_around_50_percent(self):
        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
        metis = sim.OpticalTrain(cmd)

        for filter_name in ["Lp", "Mp"]:
            metis.cmds["!OBS.filter_name"] = filter_name
            wave = np.arange(3.4, 5.3, 0.001) * u.um
            sys_trans = metis.optics_manager.system_transmission(wave)
            print(np.average(sys_trans))

            assert 0.4 < np.max(sys_trans) < 0.5

        if PLOTS:
            plt.plot(wave, sys_trans)
            plt.show()

    def test_instrument_throughput_without_atmospheric_bg(self):
        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
        metis = sim.OpticalTrain(cmd)
        metis["armazones_atmo_skycalc_ter_curve"].include = True

        src = empty_sky()
        metis.observe(src)
        img = metis.image_planes[0].data

        plt.imshow(img)
        plt.show()

    def test_print_background_contributions(self):
        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
        metis = sim.OpticalTrain(cmd)
        metis["metis_psf_img"].include = False

        metis.observe(empty_sky())

        if not PLOTS:
            plt.figure(figsize=(10, 5))
            fov = metis.fov_manager.fovs[0]
            for field in fov.fields[1:]:
                spec = fov.spectra[field.header["SPEC_REF"]]
                wave = spec.waveset
                plt.plot(wave, spec(wave), label=field.header["BG_SURF"])
            plt.legend()
            plt.show()


class TestSourceFlux:
    @pytest.mark.parametrize("mode_name", ["img_lm", "img_n"])
    def test_one_jansky_flux_is_as_expected(self, mode_name):
        """
        hmbp.in_one_jansky(metis.system_transmission) --> 2.35e6 ph / (m2 s)
        in metis (*978m2) --> 2300e6 ph / s
        """

        cmd = sim.UserCommands(use_instrument="METIS", set_modes=[mode_name])
        metis = sim.OpticalTrain(cmd)

        for eff in ["armazones_atmo_skycalc_ter_curve",   # Adds ~58000 ph/s/pix
                    "eso_combined_reflection",            # Adds ~20 ph/s/pix
                    "metis_cfo_surfaces",                 # EntrWindow alone adds ~14700 ph/s/pix
                    #"metis_img_lm_mirror_list",           # Adds ~0 ph/s/pix
                    "qe_curve",
                    "metis_psf_img"
                    ]:
            metis[eff].include = False

        src = star(flux=1*u.Jy)
        metis.observe(src)

        n = 32
        img = metis.image_planes[0].data
        img_sum = np.sum(img[1024-n:1024+n, 1024-n:1024+n])
        img_med = np.median(img[n:3*n, n:3*n])
        print(f"Sum star: {img_sum}, Median top-left: {img_med}")

        sys_trans = metis.optics_manager.system_transmission
        one_jy_phs = hmbp.in_one_jansky(sys_trans).value * 978

        if PLOTS:
            plt.imshow(img[1024-n:1024+n, 1024-n:1024+n], norm=LogNorm())
            plt.show()

        assert img_sum == approx(one_jy_phs, rel=0.05)

    def test_image_source_is_as_expected(self):
        im = face(True).astype(float)
        hdu = fits.ImageHDU(data=im)
        hdu.header.update({"CDELT1": 0.00547, "CDELT2": 0.00547,
                           "CUNIT1": "arcsec", "CUNIT2": "arcsec"})
        src = sim.Source(image_hdu=hdu, flux=1*u.mJy)

        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_n"])
        metis = sim.OpticalTrain(cmd)
        metis["detector_linearity"].include = False

        # for eff in ["armazones_atmo_skycalc_ter_curve",  # Adds ~58000 ph/s/pix
        #             "eso_combined_reflection",  # Adds ~20 ph/s/pix
        #             "metis_cfo_surfaces",  # EntrWindow alone adds ~14700 ph/s/pix
        #             "metis_img_lm_mirror_list",  # Adds ~0 ph/s/pix
        #             "qe_curve",
        #             "metis_psf_img"
        #             ]:
        #     metis[eff].include = False

        metis.observe(src)
        hdus = metis.readout()

        n = 1024
        img = metis.image_planes[0].data
        img = hdus[0][1].data
        img_sum = np.sum(img[1024 - n:1024 + n, 1024 - n:1024 + n])
        img_med = np.median(img[n:3 * n, n:3 * n])
        print(f"Sum star: {img_sum}, Median top-left: {img_med}")

        sys_trans = metis.optics_manager.system_transmission
        one_jy_phs = hmbp.in_one_jansky(sys_trans).value * 978

        if not PLOTS:
            plt.imshow(img[1024 - n:1024 + n, 1024 - n:1024 + n])  # norm=LogNorm()
            plt.show()

        assert img_sum == approx(one_jy_phs, rel=0.05)