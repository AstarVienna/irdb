from pytest import approx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import scopesim as sim
from scopesim.source.source_templates import star, empty_sky, star_field
from scopesim.source.spectrum_templates import ab_spectrum
from scopesim import rc

rc.__currsys__['!SIM.file.local_packages_path'] = "../../"

PLOTS = False


class TestMetisLss:
    def test_works(self):
        spec = ab_spectrum()
        src = sim.Source(x=[-1, 0, 1], y=[0, 0, 0],
                         ref=[0, 0, 0], weight=[1, 1, 1],
                         spectra=[spec])

        src = star(mag=0, x=0, y=0) + \
              star(mag=2, x=-2, y=0) + \
              star(mag=4, x=2, y=0)

        cmds = sim.UserCommands(use_instrument="METIS", set_modes=["lss_m"])
        cmds["!OBS.dit"] = 60
        metis = sim.OpticalTrain(cmds)

        metis["metis_psf_img"].include = False

        metis.observe(src)
        hdus = metis.readout()

        implane = metis.image_planes[0].data
        det_img = hdus[0][1].data
        assert 0 < np.sum(implane) < np.sum(det_img)

        if not PLOTS:
            plt.subplot(122)
            plt.imshow(hdus[0][1].data, origin="lower", norm=LogNorm())
            plt.title("Detctor Plane (with noise)")
            plt.colorbar()

            plt.subplot(121)
            plt.imshow(metis.image_planes[0].data, origin="lower",
                       norm=LogNorm())
            plt.title("Image Plane (noiseless)")
            plt.colorbar()
            plt.show()
