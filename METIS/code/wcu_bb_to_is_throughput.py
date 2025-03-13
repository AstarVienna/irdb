"""Utility functions for the WCU radiometry

These functions create lookup tables that are stored in the irdb.
"""
import os
from datetime import datetime
import numpy as np
from astropy.table import Table
from astropy.io import fits
from scopesim.utils import seq

def bb_to_is_throughput(rho_tube, **kwargs):
    """Compute the effective transmission through the tube between BB source
    and integrating-sphere entrance port


    """
    diam = 25.4      # diameter of the tube [mm].
    height = 28.2    # height of the tube [mm]
    drad = 0.1       # grid step in radius [mm]
    dalpha = 0.01    # grid step in "zenith angle" [rad]
    dphi = 0.02      # grid step in azimuthal angle [rad]

    alpha = seq(dalpha/2, (np.pi - dalpha)/2, dalpha)
    rad = seq(drad/2, (diam - drad)/2, drad)
    phi = seq(dphi/2, np.pi - dphi/2, dphi)

    nalpha = len(alpha)
    nrad = len(rad)
    nphi = len(phi)

    # expand to grid
    xyz = np.array(np.meshgrid(alpha, rad, phi)).reshape((3, nalpha * nrad * nphi))
    alpha = xyz[0,]
    rad = xyz[1,]
    phi = xyz[2,]
    if "special" in kwargs:
        nref = n_reflections(alpha, 0, phi, diam, height)
    else:
        nref = n_reflections(alpha, rad, phi, diam, height)

    result = np.zeros_like(rho_tube)
    for i, rho in enumerate(rho_tube):
        integrand = rho**nref * 0.5 * np.sin(2 * alpha) * rad * drad * dalpha * dphi
        result[i] = np.sum(integrand)
    return result * 16 / (np.pi * diam**2)



def n_reflections(alpha, rad, phi, diam, height):
    """Compute number of reflections of a photon emitted at radius r in direction alpha,phi"""

    beta = np.arcsin(2 * rad /diam * np.sin(phi))

    numerator = height - diam * np.sin(phi + beta)/(2 * np.sin(phi)) * np.tan(np.pi/2 - alpha)
    denominator = diam * np.cos(beta) * np.tan(np.pi/2 - alpha)
    return (np.floor(1 + numerator/denominator)).astype(int)


#def integrating_sphere(wavelength):
#    """Compute the magnification factor due to the integrating sphere"""


def make_pri_hdu():
    """Create primary header with meta data"""
    pri_hdu = fits.PrimaryHDU()

    meta = {"author": "Oliver Czoske",
            "descript": "METIS WCU, throughput from Blackbody to integrating sphere",
            "source": "E-REP-MPIA-MET-1203",
            "date-cre": "2024-11-19",
            "date-mod": datetime.today().strftime("%Y-%m-%d"),
            "status": "model",
            "code": os.path.basename(__file__)
            }
    pri_hdu.header.update(meta)
    return pri_hdu

def do_main():
    """Create and write out lookup table for BB to IS transfer"""
    rho_tube = seq(0, 1, 0.02)
    t_general_no_gap = bb_to_is_throughput(rho_tube)
    t_special_no_gap = bb_to_is_throughput(rho_tube, special=True)

    arr = {"rho_tube": rho_tube,
           "t_gen_no_gap": t_general_no_gap,
           "t_spec_no_gap": t_special_no_gap}
    tab = Table(arr)
    table_hdu = fits.table_to_hdu(tab)
    table_hdu.header["EXTNAME"] = "BB_to_IS_throughput"
    pri_hdu = make_pri_hdu()
    hdul = fits.HDUList([pri_hdu, table_hdu])
    hdul.writeto("WCU_BB_to_IS_throughput.fits", overwrite=True)



if __name__ == "__main__":
    do_main()
