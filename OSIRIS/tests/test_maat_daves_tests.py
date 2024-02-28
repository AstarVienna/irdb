from pathlib import Path
import pytest

import scopesim as sim
from astropy import units as u
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from scopesim_templates.extragalactic import galaxy
from scopesim_templates.misc.misc import point_source
from scopesim_templates.misc.misc import uniform_source
from synphot import SourceSpectrum

PLOTS = False

PATH_HERE = Path(__file__).parent
sim.rc.__config__["!SIM.file.local_packages_path"] = str(PATH_HERE.parent.parent)


@pytest.mark.slow
def test_maat_runs_with_point_source():
    g191 = SourceSpectrum.from_file(str(PATH_HERE / 'test_data' / 'fg191b2b.dat'))
    src = point_source(sed=g191, filter_curve='V',
                       amplitude=11.78 * u.ABmag, x=3, y=2.1)

    cmds = sim.UserCommands(use_instrument="OSIRIS", set_modes=["MAAT"])
    cmds["!ATMO.seeing"] = 1.
    cmds["!OBS.exptime"] = 80
    cmds["!OBS.dit"] = 80
    cmds["!OBS.ndit"] = 1
    cmds["!OBS.airmass"] = 1.2
    cmds["!OBS.grating_name"] = 'R2000B'

    osiris = sim.OpticalTrain(cmds)
    osiris.observe(src)

    if PLOTS:
        plt.imshow(osiris.image_planes[0].data, norm=LogNorm())
        plt.show()


@pytest.mark.slow
def test_maat_runs_with_extended_source():
    src = galaxy("kc96/s0", z=0.1, amplitude=12*u.mag, filter_curve="V",
                 pixel_scale=0.1, r_eff=3.5, n=2, ellip=0.3, theta=45, extend=5)

    cmds = sim.UserCommands(use_instrument="OSIRIS", set_modes=["MAAT"])
    cmds["!ATMO.seeing"] = 1.
    cmds["!OBS.exptime"] = 80
    cmds["!OBS.dit"] = 80
    cmds["!OBS.ndit"] = 1
    cmds["!OBS.airmass"] = 1.2
    cmds["!OBS.grating_name"] = 'R2000B'

    osiris = sim.OpticalTrain(cmds)
    osiris.observe(src)

    if PLOTS:
        plt.imshow(osiris.image_planes[0].data)
        plt.show()


@pytest.mark.slow
def test_maat_runs_with_line_list_source():
    arcspec = SourceSpectrum.from_file(str(PATH_HERE / 'test_data' / 'OSIRIS_stitchedArc.dat'))
    arc = uniform_source(sed=arcspec, filter_curve='V', amplitude=16*u.ABmag, extend=520)

    cmds = sim.UserCommands(use_instrument="OSIRIS", set_modes=["MAAT"])
    cmds["!OBS.exptime"] = 60
    cmds["!OBS.dit"] = 60
    cmds["!OBS.ndit"] = 1
    cmds["!OBS.grating_name"] = 'R2000B'

    osiris = sim.OpticalTrain(cmds)
    osiris["lapalma_skycalc_curves"].include = False
    osiris.observe(arc)

    if PLOTS:
        plt.imshow(osiris.image_planes[0].data, norm=LogNorm())
        plt.show()
