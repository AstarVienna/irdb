from os import path as pth
import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt
import scopesim as sim
from scopesim import rc

TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../"))
rc.__search_path__ += [TOP_PATH]

PLOTS = True


def test_eso_vs_scopesim_throughput():
    sl = sim.effects.SurfaceList(filename="LIST_mirrors_ELT.tbl")
    wave = np.linspace(0.3, 2.5, 100) * u.um
    plt.plot(wave, sl.throughput(wave), label="ScopeSim")

    ter = sim.effects.TERCurve(filename="TER_ELT_System_20190611.dat")

    if PLOTS:
        plt.plot(wave, ter.surface.reflection(wave), label="ESO-253082")

        plt.legend(loc=4)
        plt.show()


def test_eso_vs_scopesim_emission():
    rc.__currsys__["!ATMO.temperature"] = 0.
    rc.__currsys__["!TEL.etendue"] = (1 * u.m * u.arcsec)**2

    sl = sim.effects.SurfaceList(filename="LIST_mirrors_ELT.tbl")
    ter = sim.effects.TERCurve(filename="TER_ELT_System_20190611.dat",
                               temperature="!ATMO.temperature")

    wave = np.linspace(0.3, 2.5, 100) * u.um
    sl_flux = sl.emission(wave)
    ter_flux = ter.surface.emission(wave)

    if PLOTS:

        plt.plot(wave, sl_flux, label="ScopeSim")
        plt.plot(wave, ter_flux, label="ESO-253082")

        plt.semilogy()
        plt.legend(loc=2)
        plt.ylim(ymin=1e-10)
        plt.show()
