import os.path as pth

import pytest
from astropy.io import fits
from astropy.wcs import WCS
from matplotlib import pyplot as plt

from scopesim.effects import SpectralTraceList
from scopesim.tests.mocks.py_objects import header_objects as ho
from scopesim import rc

pytest.skip(allow_module_level=True)

PLOTS = False
DATA_DIR = pth.abspath(pth.join(pth.dirname(__file__), "../"))
rc.__search_path__.insert(0, DATA_DIR)


class TestInit:
    def test_initialises_with_a_hdulist(self):
        spt = SpectralTraceList(
            filename="TRACE_SCI_3arcsec.fits",
            x_colname="x0",
            y_colname="y0",
            s_colname="s0",
        )
        assert isinstance(spt, SpectralTraceList)
        assert spt.get_data(2, fits.BinTableHDU)

    @pytest.mark.xfail(reason="butchered by changes in spectral_trace_list[_utils].py")
    def test_gets_headers_from_real_file(self):
        slit_hdr = ho._long_micado_slit_header()
        # slit_hdr = ho._short_micado_slit_header()
        wave_min = 0.8
        wave_max = 2.5
        spt = SpectralTraceList(
            filename="TRACE_SCI_15arcsec.fits",
            x_colname="x0",
            y_colname="y0",
            s_colname="s0",
        )

        params = {"wave_min": wave_min, "wave_max": wave_max,
                  "pixel_scale": 0.004, "plate_scale": 0.266666667}
        hdrs = spt.get_fov_headers(slit_hdr, **params)
        assert isinstance(spt, SpectralTraceList)

        print(len(hdrs))

        if PLOTS:
            spt.plot(wave_min, wave_max)

            # pixel coords
            for hdr in hdrs[::300]:
                xp = [0, hdr["NAXIS1"], hdr["NAXIS1"], 0]
                yp = [0, 0, hdr["NAXIS2"], hdr["NAXIS2"]]
                wcs = WCS(hdr, key="D")
                # world coords
                xw, yw = wcs.all_pix2world(xp, yp, 1)
                plt.plot(xw, yw, alpha=0.2)
            plt.show()
