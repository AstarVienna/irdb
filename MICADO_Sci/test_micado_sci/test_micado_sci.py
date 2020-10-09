from os import path as pth
import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt
import scopesim as sim

TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../../"))


def test_elt_ter_curve_reads_in():
    filename = pth.join(TOP_PATH, "MICADO_Sci", "TER_ELT_System_20190611.dat")
    elt = sim.effects.TERCurve(filename=filename)
    assert isinstance(elt, sim.effects.TERCurve)

    wave = np.arange(0.3, 2.5, 0.001) * u.um
    plt.plot(wave, elt.surface.reflection(wave))
    plt.show()


def test_scao_1_5mas_works():
    pass


def test_mcao_4mas_works():
    pass


def test_spec_for_a_specific_wavelength_range_works():
    pass
