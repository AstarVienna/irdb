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


from pytest import approx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from astropy import units as u

import scopesim as sim
from scopesim.source.source_templates import star, empty_sky
from scopesim.source import source_templates as st
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
        metis["metis_psf_img"].include = False

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
                          # "armazones_atmo_skycalc_ter_curve",
                          # "eso_combined_reflection",
                          # "metis_cfo_surfaces",
                          # "metis_img_lm_mirror_list",
                          # "qe_curve",
                          # "metis_psf_img",
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
                          "armazones_atmo_skycalc_ter_curve",
                          "eso_combined_reflection",
                          "metis_cfo_surfaces",
                          # "metis_img_lm_mirror_list",
                          # "qe_curve",
                          #"metis_psf_img"
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

    def test_slit_losses(self):
        src = star(flux=1 * u.Jy)

        cmds_lss = sim.UserCommands(use_instrument="METIS", set_modes=["lss_l"])
        metis_lss = sim.OpticalTrain(cmds_lss)
        metis_lss["lss_spectral_traces"].include = False
        metis_lss["armazones_atmo_skycalc_ter_curve"].include = False
        metis_lss["eso_combined_reflection"].include = False
        metis_lss["metis_cfo_surfaces"].include = False

        metis_lss.observe(src)

        cmds_img = sim.UserCommands(use_instrument="METIS", set_modes=["lss_l"])
        metis_img = sim.OpticalTrain(cmds_img)
        metis_img["lss_spectral_traces"].include = False
        metis_img["armazones_atmo_skycalc_ter_curve"].include = False
        metis_img["eso_combined_reflection"].include = False
        metis_img["metis_cfo_surfaces"].include = False
        metis_img["slit_wheel"].include = False

        metis_img.observe(src)

        n = 32
        img_slit = metis_lss.image_planes[0].data[1024-n:1024+n, 1024-n:1024+n]
        img_normal = metis_img.image_planes[0].data[1024-n:1024+n, 1024-n:1024+n]

        plt.subplot(211)
        plt.imshow(img_slit, origin="lower", norm=LogNorm(), vmin=1e-8)
        plt.title(img_slit.sum())

        plt.subplot(212)
        plt.imshow(img_normal, origin="lower", norm=LogNorm(), vmin=1e-8)
        plt.title(img_normal.sum())

        plt.show()

    def test_delta_function_psf_for_random_spectroscopy_jumps(self):
        sim_src = sim.source.source_templates.star(flux=0 * u.mag)

        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["lss_m"])
        metis = sim.OpticalTrain(cmd)
        # metis["metis_psf_img"]._file[1].data = metis["metis_psf_img"]._file[2].data

        # kernel = np.zeros([7, 7])
        # kernel[1:6, 1:6] = 0.05
        # kernel[2:5, 2:5] = 0.1
        # kernel[3, 3] = 0.5
        # metis["metis_psf_img"]._file[1].data = kernel
        # metis["metis_psf_img"]._file[2].data = kernel
        #
        # for i, fov in enumerate(metis.fov_manager.fovs):
        #     psf = metis["metis_psf_img"].get_kernel(fov)
        #     plt.subplot(1, 2, i+1)
        #     plt.imshow(psf)
        #     plt.title(f"{psf.sum()}")
        #     plt.colorbar()
        # plt.show()

        metis.observe(sim_src)
        img_src = metis.image_planes[0].data[:, 1016:1024]
        img_bg = metis.image_planes[0].data[:, 816:824]

        plt.semilogy(np.sum(img_src, axis=1))
        plt.semilogy(np.sum(img_bg, axis=1))
        plt.show()

    def test_HL_tau(self):
        from astropy.io import fits
        hdul = fits.open(r"F:\temp\scopesim_metis_workshop\HL_Tau_prep_for_Scopesim.fits")
        src = sim.Source(image_hdu=hdul[1], flux=1*u.MJy)

        cmd = sim.UserCommands(use_instrument='METIS', set_modes=['img_n'])
        metis = sim.OpticalTrain(cmd)
        metis['detector_linearity'].include = False

        metis.observe(src, update=True)

        img = metis.image_planes[0].data
        img = metis.readout()[0][1].data

        plt.imshow(img)
        plt.show()

    def test_roys_cube(self):
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.colors import LogNorm

        from astropy import units as u
        from astropy.io import fits

        import scopesim as sim

        sim.rc.__currsys__["!SIM.file.local_packages_path"] = "F:/Work/irdb"

        fname = r"F:\temp\scopesim_metis_workshop\models_Lband_HD100546_gap100.cube_rebinned.fits"
        hdulist = fits.open(fname)

        hdr = hdulist[0].header
        hdr_info = {"CDELT1": hdr["PFOV"],
                    "CDELT2": hdr["PFOV"],
                    "CDELT3": 0.02,
                    "CUNIT3": "um",
                    "CRPIX3": 0,
                    "CRVAL3": 3.10,
                    "CTYPE3": "WAVE",
                    "CUNIT1": "arcsec",
                    "CUNIT2": "arcsec",
                    "BUNIT": "Jy",
                    }
        hdulist[0].header.update(hdr_info)

        src = sim.Source(image_hdu=hdulist[0], flux=1 * u.Jy)

        cmd = sim.UserCommands(use_instrument="METIS", set_modes=["lss_l"])
        metis = sim.OpticalTrain(cmd)

        metis.observe(src)

        img = metis.image_planes[0].data

        plt.imshow(img)
        plt.show()

    def test_compare_anisocado_psf_to_metis_psf(self):
        import anisocado
        psf = anisocado.AnalyticalScaoPsf(N=512, wavelength=3.8,
                                          pixelSize=0.00765457,
                                          profile_name="EsoQ1")
        psf_an = psf.make_psf()
        psf_an /= psf_an.sum()

        from astropy.io import fits
        psf_im = fits.getdata("../PSF_SCAO_9mag_06seeing.fits", ext=2)[256:768, 256:768]
        psf_im /= psf_im.sum()

        plt.subplot(131)
        plt.imshow(psf_an, norm=LogNorm(vmin=1e-7))
        plt.colorbar()

        plt.subplot(132)
        plt.imshow(psf_im, norm=LogNorm(vmin=1e-7))
        plt.colorbar()

        plt.subplot(133)
        plt.imshow(np.abs(psf_im / psf_an - 1), vmax=1)
        plt.colorbar()

        plt.show()

