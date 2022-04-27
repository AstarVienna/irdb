"""
To do
-----
Sky background fluxes don't match with Roy's flux document
- test_sky_phs_with_full_system_transmission

Work out whether the flux components are realistic
- TestSourceFlux

"""
import pytest
pytest.skip("we'll come back to this one day (hopefully)",
            allow_module_level=True)

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

        if PLOTS:
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
        cmd["!ATMO.pwv"] = 1.0
        cmd["!ATMO.airmass"] = 1.0
        cmd["!ATMO.temperature"] = 258

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
        metis["skycalc_atmosphere"].include = True

        src = empty_sky()
        metis.observe(src)
        img = metis.image_planes[0].data

        plt.imshow(img)
        plt.show()

    def test_print_background_contributions(self):
        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
        metis = sim.OpticalTrain(cmd)
        metis["psf"].include = False

        metis.observe(empty_sky())

        if PLOTS:
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

        for eff in ["skycalc_atmosphere",   # Adds ~58000 ph/s/pix
                    "telescope_reflection", # Adds ~20 ph/s/pix
                    "common_fore_optics",   # EntrWindow alone adds ~14700 ph/s/pix
                    #"metis_img_lm_mirror_list",           # Adds ~0 ph/s/pix
                    "quantum_efficiency",
                    "psf"
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

        # for eff in ["skycalc_atmosphere",  # Adds ~58000 ph/s/pix
        #             "telescope_reflection",  # Adds ~20 ph/s/pix
        #             "common_fore_optice",  # EntrWindow alone adds ~14700 ph/s/pix
        #             "metis_img_lm_mirror_list",  # Adds ~0 ph/s/pix
        #             "quantum_efficiency",
        #             "psf"
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

        if PLOTS:
            plt.imshow(img[1024 - n:1024 + n, 1024 - n:1024 + n])  # norm=LogNorm()
            plt.show()

        assert img_sum == approx(one_jy_phs, rel=0.05)

    def test_image_is_visible(self):
        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_n"])
        metis = sim.OpticalTrain(cmd)
        for eff in ["skycalc_atmosphere",   # Adds ~58000 ph/s/pix
                    "telescope_reflection", # Adds ~20 ph/s/pix
                    "common_fore_optics",   # EntrWindow alone adds ~14700 ph/s/pix
                    "chop_nod",
                    # "metis_img_lm_mirror_list",           # Adds ~0 ph/s/pix
                    # "quantum_efficiency",
                    "psf"
                    ]:
            metis[eff].include = False

        hdu = fits.open(r"F:\temp\scopesim_metis_workshop\data\sd0490_image_l12_i090_p000.fits")
        hdu[0].header["CDELT1"] *= 10
        hdu[0].header["CDELT2"] *= 10
        hdu[0].header["CUNIT1"] = "deg"
        hdu[0].header["CUNIT2"] = "deg"
        hdu[0].header["CRVAL1"] = 0
        hdu[0].header["CRVAL2"] = 0
        src = sim.Source(image_hdu=hdu[0], flux=1*u.Jy)
        # src = empty_sky()

        metis.observe(src)
        img = metis.image_planes[0].data

        if PLOTS:
            plt.imshow(img)
            plt.show()


def simulate_point_source(plot=False):
    '''Create a simulation of a point source'''

    print("------ Beginning of simulate_point_source() ----------")
    # Create the Source object, this is currently a hack. We create a
    # spectrum that is flat in lambda with magnitude 0 in the Lp
    # filter. For this purpose we are currently using a function in
    # SimMETIS, pending its inclusion in ScopeSim-Templates.

    # import simmetis
    # dummycmd = simmetis.UserCommands("metis_image_LM.config",
    #                                  sim_data_dir="../data")
    # dummycmd["INST_FILTER_TC"] = "TC_filter_Lp.dat"
    #
    # lam, spec = simmetis.source.flat_spectrum(0,
    #                                           dummycmd["INST_FILTER_TC"])

    lam = np.linspace(1, 20, 0.001)
    spec = np.ones(len(lam)) * 1e7      # 0 mag spectrum

    if plot:
        plt.plot(lam, spec)
        plt.xlabel(r"$\lambda$ [um]")
        plt.ylabel("relative flux")
        plt.title("Spectrum of input source")
        plt.show()

    # Create two source objects for two dither positions
    dither_offset = 1
    src = sim.Source(lam=lam * u.um, spectra=np.array([spec]),
                          ref=[0], x=[0], y=[0])
    src_dither = sim.Source(lam=lam * u.um, spectra=np.array([spec]),
                                 ref=[0], x=[0], y=[dither_offset])

    # Load the configuration for the METIS LM-band imaging mode.
    cmd = sim.UserCommands(use_instrument="METIS",
                                set_modes=["img_lm"])

    # build the optical train and adjust
    metis = sim.OpticalTrain(cmd)
    metis['detector_linearity'].include = False

    # Set the DIT to 1 second
    metis.cmds["!OBS.dit"] = 1.

    # Perform an observation.
    metis.observe(src, update=True)
    hdus = metis.readout()

    metis.observe(src_dither, update=True)
    hdus_dither = metis.readout()

    frame1 = hdus[0][1].data
    frame2 = hdus_dither[0][1].data
    if plot:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 6),
                                       sharey=True)
        f1_plot = ax1.imshow(frame1[900:1400, 940:1100], origin='lower')
        fig.colorbar(f1_plot, ax=ax1)

        f2_plot = ax2.imshow(frame2[900:1400, 940:1100], origin='lower')
        fig.colorbar(f2_plot, ax=ax2)

        plt.show()

    # Shift the dithered image back to the original position and combine
    # the two images
    pixscale = metis.cmds['INST']['pixel_scale']
    frame_sum = frame1 + np.roll(frame2,
                                 np.int(np.round(-dither_offset / pixscale)),
                                 axis=0)
    if plot:
        plt.imshow(frame_sum[940:1100, 940:1100])
        plt.colorbar()
        plt.show()

    print("Writing test_LM_framesum.fits")
    fits.writeto("test_LM_framesum.fits", frame_sum, overwrite=True)

    print("--------- End of simulate_point_source() -------------")


def vary_exposure_times(plot=False):
    '''Adjusting exposure times'''
    print("------ Beginning of vary_exposure_times() ----------")

    # Create a new source
    # import simmetis
    # dummycmd = simmetis.UserCommands("metis_image_LM.config",
    #                                  sim_data_dir="../data")
    # lam, spec = simmetis.source.flat_spectrum(17, "TC_filter_Lp.dat")

    lam = np.arange(1, 20, 0.001)
    spec = np.ones(len(lam)) * 1e7 * 2.5*np.log10(-30)     # 0 mag spectrum

    src = sim.Source(lam=lam * u.um, spectra=np.array([spec]),
                          ref=[0], x=[0], y=[0])

    # Load the configuration for the METIS LM-band imaging mode.
    cmd = sim.UserCommands(use_instrument="METIS",
                           set_modes=["img_lm"])

    # build the optical train and adjust
    metis = sim.OpticalTrain(cmd)
    metis['detector_linearity'].include = False

    # Observe the source
    metis.observe(src, update=True)

    # Readout with a range of DITs and NDITs
    dit = np.array([1, 1, 1, 10, 10, 10, 100, 100, 100])
    ndit = np.array([3, 10, 30, 3, 10, 30, 3, 10, 30])
    hdus = list()
    for i in range(9):
        metis.cmds["!OBS.dit"] = dit[i]
        metis.cmds["!OBS.ndit"] = ndit[i]
        thehdu = metis.readout()[0]
        hdus.append(thehdu)
        print(i, "DIT =", rc.__currsys__["!OBS.dit"],
              "   NDIT =", rc.__currsys__["!OBS.ndit"])
        print("min =", thehdu[1].data.min(), "    max =", thehdu[1].data.max())

    if plot:
        fig, axes = plt.subplots(3, 3, figsize=(12, 12),
                                 sharex=True, sharey=True)
        for i in range(9):
            theax = axes.flat[i]
            frame = hdus[i][1].data[960:1090, 960:1090]
            theplot = theax.imshow(frame, origin='lower')
            fig.colorbar(theplot, ax=theax)
            theax.set_title("DIT={}, NDIT={}, INTTIME={}".format(
                dit[i], ndit[i], dit[i] * ndit[i]))

        plt.show()


    # Perform photometry
    aperture = CircularAperture([(1024., 1024.)], r=10.)

    bglevel = np.zeros(9)
    bgnoise = np.zeros(9)
    starsum = np.zeros(9)
    starnoise = np.zeros(9)

    for i, thehdu in enumerate(hdus):
        # background stats
        bglevel[i] = np.mean(thehdu[1].data[0:800, 0:800])
        bgnoise[i] = np.std(thehdu[1].data[0:800, 0:800])
        # total signal of star
        phot_table = aperture_photometry(thehdu[1].data - bglevel[i], aperture,
                                         error=(np.ones_like(thehdu[1].data)
                                                * bgnoise[i]))
        starsum[i] = phot_table['aperture_sum'][0]
        starnoise[i] = phot_table['aperture_sum_err'][0]

    table = Table([dit, ndit, dit * ndit, bglevel, bgnoise, starsum,
                   starsum / starnoise],
                  names=["DIT", "NDIT", "INTTIME", "bg level", "bg noise",
                         "Star counts", "S/N"])
    table["bg level"].format = ".0f"
    table["bg noise"].format = ".1f"
    table["Star counts"].format = ".1f"
    table["S/N"].format = ".2f"

    table.pprint()

    if plot:
        plt.plot(table["INTTIME"], table["S/N"], "o")
        plt.xlabel("Integration time")
        plt.ylabel("Signal-to-noise ratio")
        plt.show()

    print("--------- vary_exposure_times() -------------")
