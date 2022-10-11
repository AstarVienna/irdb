from os import path as p
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
from astropy import units as u

from synphot import SourceSpectrum
from scopesim_templates.misc.misc import point_source
import scopesim as sim
from scopesim.effects import SpectralTraceList
from scopesim.optics import FieldOfView

sim.rc.__config__["!SIM.file.local_packages_path"] = "../../"

PLOTS = False


class TestMaatTraces:
    def test_plot_traces(self):
        """
        Test that the input trace description maps 1:1 to the output trace image
        """
        from scopesim_templates.misc.misc import uniform_source
        arcspec = SourceSpectrum.from_file('test_data/OSIRIS_stitchedArc.dat')
        arc = uniform_source(sed=arcspec, filter_curve='V',
                             amplitude=16 * u.ABmag, extend=520)

        cmds = sim.UserCommands(use_instrument="OSIRIS", set_modes=["MAAT"])
        cmds.cmds["!OBS.exptime"] = 60
        cmds.cmds["!OBS.dit"] = 60
        cmds.cmds["!OBS.ndit"] = 1
        cmds.cmds["!OBS.grating_name"] = 'R2000B'

        osiris = sim.OpticalTrain(cmds)
        osiris["lapalma_skycalc_curves"].include = False
        osiris.observe(arc)

        plt.imshow(osiris.image_planes[0].data, norm=LogNorm())

        # -----------------------------

        clrs = "rgbcmyk" * 10
        sptl = SpectralTraceList(filename="../MAAT_traces/R2000B_MAAT_TRACE.fits",
                                 wave_colname="wavelength",
                                 s_colname="xi",
                                 col_number_start=1)
        i = 0
        for key, trace in sptl.spectral_traces.items():
            c = clrs[i]
            x = trace.table["x"] / 0.015 + 2048
            y = trace.table["y"] / 0.015 + 2048
            plt.plot(x, y, c)

            waves = np.linspace(trace.wave_min, trace.wave_max, 20)
            slit_coords = [-5, 5]
            x = trace.xilam2x(slit_coords, waves, grid=True) / 0.015 + 2048
            y = trace.xilam2y(slit_coords, waves, grid=True) / 0.015 + 2048
            plt.plot(x, y, f"{c}.")
            i += 1

        plt.show()
