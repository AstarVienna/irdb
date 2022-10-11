from os import path as p
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

from scopesim.effects import SpectralTraceList
from scopesim.optics import FieldOfView

class TestMaatTraces:
    def test_plot_traces(self):
        clrs = "rgbcmyk"*10
        sptl = SpectralTraceList(filename="../MAAT_traces/R2000B_MAAT_TRACE.fits",
                                 wave_colname="wavelength",
                                 s_colname="xi",
                                 col_number_start=1)
        i = 0
        for key, trace in sptl.spectral_traces.items():
            c = clrs[i]
            plt.plot(trace.table["x"], trace.table["y"], c)

            waves = np.linspace(trace.wave_min, trace.wave_max, 20)
            slit_coords = [0, 10]
            x = trace.xilam2x(slit_coords, waves, grid=True)
            y = trace.xilam2y(slit_coords, waves, grid=True)
            plt.plot(x, y, f"{c}.")
            i += 1

        plt.xlim(-30.72, 30.72)
        plt.ylim(-30.72, 30.72)
        plt.gca().set_aspect("equal")
        plt.show()


    def test_projects_fov(self):
        fov = FieldOfView()

