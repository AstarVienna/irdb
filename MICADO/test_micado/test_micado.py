import pytest
from time import time
from os import path as pth

import numpy as np
import matplotlib.pyplot as plt
from astropy import units as u
from astropy.table import Table

from scopesim import rc, OpticalTrain
from scopesim.effects import SurfaceList, TERCurve
from scopesim.effects.data_container import DataContainer

PLOTS = False

DATA_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))
rc.__currsys__["!SIM.local_packages_path"] = DATA_DIR


class TestSurfaceLists:
    def test_speed_of_micado_common_surfacelist(self):
        area = 978 * u.m ** 2
        sl = SurfaceList(filename="LIST_MICADO_mirrors_static.dat",
                         etendue=area * (0.004*u.arcsec)**2, area=area)
        wave = np.arange(0.3, 2.5, 0.001) * u.um

        start = time()
        thru = sl.throughput(wave)
        flux = sl.emission(wave)
        end = time()
        print(end - start)

        if PLOTS:
            plt.plot(wave, flux)
            plt.show()

        assert end - start < 0.5
        assert np.max(thru) > 0.7
        assert np.max(flux) > 0.

    def test_speed_of_single_tercurve_for_micado_common_optics(self):
        ter = TERCurve(filename="TER_MICADO_mirror_mgf2agal.dat",
                       etendue=978 * u.m ** 2 * (0.004*u.arcsec)**2,
                       area=1*u.m**2, temperature=-190*u.deg_C)
        wave = np.arange(0.3, 2.5, 0.0015) * u.um

        start = time()
        thru = ter.throughput(wave)
        flux = ter.emission(wave)
        end = time()
        print(end - start)

        assert end - start < 0.5
        assert np.max(thru) > 0.7
        assert np.max(flux) > 0.

    def test_plot_throughputs_of_all_surface_lists(self):
        pass


class TestMicadoLoadsOpticalTrain:
    def just_loads(self):
        micado = OpticalTrain("MICADO")
        assert isinstance(micado, OpticalTrain)
