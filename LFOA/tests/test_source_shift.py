"""Test Source.shift by doing an integration test with LFAO."""
import pytest
import os
from os import path as pth
import shutil

import numpy
import scipy
from astropy import units as u
from numpy.testing import assert_approx_equal

import scopesim
from scopesim import rc
import scopesim_templates as sim_tp

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm


if rc.__config__["!SIM.tests.run_integration_tests"] is False:
    pytestmark = pytest.mark.skip("Ignoring LFAO integration tests")

TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH
rc.__config__["!SIM.file.use_cached_downloads"] = False

PKGS = {"LFOA": "telescopes/LFOA.zip"}

PLOTS = False
# rc.__config__["!SIM.file.local_packages_path"] = "./lfoa_temp/"
# CLEAN_UP = False
#
#
# def setup_module():
#     """Download packages."""
#     rc_local_path = rc.__config__["!SIM.file.local_packages_path"]
#     if not os.path.exists(rc_local_path):
#         os.mkdir(rc_local_path)
#         rc.__config__["!SIM.file.local_packages_path"] = os.path.abspath(
#             rc_local_path)
#
#     for pkg_name in PKGS:
#         if not os.path.isdir(os.path.join(rc_local_path, pkg_name)) and \
#                 "irdb" not in rc_local_path:
#             scopesim.download_packages(PKGS[pkg_name])
#
#
# def teardown_module():
#     """Delete packages."""
#     rc_local_path = rc.__config__["!SIM.file.local_packages_path"]
#     if CLEAN_UP and "irdb" not in rc_local_path:
#         shutil.rmtree(rc_local_path)


@pytest.mark.slow
class TestShiftSource:
    def test_shift_lfao(self):
        # core_radius = 0.6 to ensure it fits the image after shifting
        src = sim_tp.stellar.cluster(mass=1000, distance=2000,
                                         core_radius=0.6,)

        lfoa = scopesim.OpticalTrain("LFOA")
        lfoa.observe(src)
        hdulists1 = lfoa.readout()

        data1 = hdulists1[0][1].data
        data = data1
        dmin, dmax, dmean, dmed, dstd = data.min(), data.max(), data.mean(), numpy.median(data), data.std()

        # Do some filtering before finding the center of the cluster.
        data1a = (data1 - dmed)
        data1a[data1a < 0] = 0
        cm1y, cm1x = scipy.ndimage.center_of_mass(data1a)
        print(cm1y, cm1x)

        if PLOTS:
            plt.imshow(data, norm=LogNorm(vmin=dmed, vmax=dmed + 0.1 * dstd))
            plt.colorbar()
            plt.show()

        # Shift the cluster.
        dx = 10 * u.arcsec
        dy = 20 * u.arcsec
        src.shift(dx=dx, dy=dy)

        lfoa = scopesim.OpticalTrain("LFOA")
        lfoa.observe(src)
        hdulists2 = lfoa.readout()

        data2 = hdulists2[0][1].data
        data = data2
        dmin, dmax, dmean, dmed, dstd = data.min(), data.max(), data.mean(), numpy.median(data), data.std()

        if PLOTS:
            plt.imshow(data, norm=LogNorm(vmin=dmed, vmax=dmed + 0.1 * dstd))
            plt.colorbar()
            plt.show()

        data2a = (data2 - dmed)
        data2a[data2a < 0] = 0

        cm2y, cm2x = scipy.ndimage.center_of_mass(data2a)
        print(cm2y, cm2x)

        # Compare the center of masses. Centers of mass. Centers of masses...
        dxmp = cm2x - cm1x
        dymp = cm2y - cm1y
        print(dxmp, dymp)

        # 0.307 is pixel_scale
        # 2 is the binning
        dxm = dxmp * 0.307 * 2
        dym = dymp * 0.307 * 2
        print(dxm, dym)

        # E.g. 10.0 == 10.1.
        assert_approx_equal(dxm, dx.value, 1)
        assert_approx_equal(dym, dy.value, 1)
