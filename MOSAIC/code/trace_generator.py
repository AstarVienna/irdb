"""This module intent to easily generate Trace file for MOSAIC
:author: Clément Hottier
"""
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.table import Table


class TraceGenerator:
    
    def __init__(self,
                 l_low: float=1.4,      # um
                 l_high: float=1.91,     # um
                 delta_lambda: float=0.183e-3*2,      # um
                 sampling: float=2.56,  # pixels
                 pixel_size: float=0.015,  # mm
                 trace_distances=8,  # pixels
                 fiber_per_mos: int=7,
                 nbr_mos: int=2,
                 mos_distance: float=32,  # pixels
                 ):
        """Build a trace Generator. 

        :param l_low: the minimum wavelength of the trace , defaults to 0.770
        :type l_low: float, optional
        :param l_high: the maximum lambda of the trace , defaults to 1.063
        :type l_high: float, optional
        :param delta_lambda: delta lambda of the trace, defaults to 0.183
        :type delta_lambda: float, optional
        :param sampling: sampling in pixels, defaults to 2.56
        :type sampling: float, optional
        :param fiber_per_mos: number of fiber per mos, optinonal
        :type fiber_per_mos: int, defaults to 7
        :param nbr_mos: number of mos, defaults to 2
        :type nbr_mos: int, optional
        :param mos_distance: distances between 2 mos in pixel, defaults to 32
        :type mos_distance: float, optional
        """
        self._l_low = l_low
        self._l_high = l_high
        self._delta_lambda = delta_lambda
        self._sampling = sampling
        self._pixel_size = pixel_size
        self._trace_distance = trace_distances
        self._fiber_per_mos = fiber_per_mos
        self._nbr_mos = nbr_mos
        self._mos_distance = mos_distance

        self._set_xmos()
        self._set_wavelength()
        self._set_y()
        self._set_x()

    def _set_xmos(self):
        self._xmos = np.arange(self._fiber_per_mos) * self._trace_distance * self._pixel_size

    def _set_wavelength(self):
        self._wavelengths = np.arange(self._l_low, self._l_high, self._delta_lambda)
    
    def _set_y(self):
        # self._y = np.linspace(-30.72, 30.72, self._wavelengths.size)

        self._y = np.arange(self._wavelengths.size) * self._sampling * self._pixel_size
        self._y = self._y - (self._y[-1] - self._y[0])/2
    
    def _set_x(self):
        tmp = [self._xmos]
        for i in range(1,self._nbr_mos):
            locx = self._xmos + tmp[-1].max() + self._mos_distance * self._pixel_size
            tmp += [locx]
        self._x = np.concatenate(tmp)
        self._x = self._x - (self._x[-1] - self._x[0])/2
    
    def _generate_trace(self,id:int) -> pd.DataFrame:
        res = pd.DataFrame({"wavelength":self._wavelengths, "y":self._y})
        res["x"] = self._x[id]
        return res

    def _generate_trace_descriptor(self,) -> pd.DataFrame:
        res = pd.DataFrame({"aperture_id":np.arange(self._x.size)})
        res["description"] = [f"Trace_Ap{i}" for i in res["aperture_id"]]
        res["extension_id"] = res["aperture_id"] + 2
        res["image_plane_id"] = 0
        return res.loc[:,["description", "extension_id", "aperture_id","image_plane_id"]]
    
    def to_fits(self, path:str) -> None:
        li = [fits.PrimaryHDU(), fits.BinTableHDU(Table.from_pandas(self._generate_trace_descriptor()))]
        li = li + [fits.BinTableHDU(Table.from_pandas(self._generate_trace(i))) for i in range(self._x.size)]
        hdul = fits.HDUList(li)
        hdul.writeto(path,overwrite=True)


if __name__ =="__main__":
    t = TraceGenerator()
    t.to_fits("../TRACE_MOSAIC_MOS_NIR_LR_H.fits")