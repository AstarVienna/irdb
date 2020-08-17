from os import path as pth
import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt
import scopesim as sim
from scopesim import rc

TOP_PATH = pth.abspath(pth.join(pth.dirname(__file__), "../../"))
rc.__config__["!SIM.file.local_packages_path"] = TOP_PATH


def test_elt_ter_curve_reads_in():
    filename = pth.join(TOP_PATH, "MICADO_Sci", "TER_ELT_System_20190611.dat")
    elt = sim.effects.TERCurve(filename=filename)
    assert isinstance(elt, sim.effects.TERCurve)

    wave = np.arange(0.3, 2.5, 0.001) * u.um
    plt.plot(wave, elt.surface.reflection(wave))
    plt.show()


def test_reads_in_default_yaml():
    cmd = sim.UserCommands(use_instrument="MICADO_Sci")
    print(cmd)




