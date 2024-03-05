"""Unit tests for irdb/ELT"""
# pylint: disable=no-self-use, missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import pytest
import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt
import scopesim as sim
from scopesim import rc
from scopesim import UserCommands

TOP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
rc.__search_path__ += [TOP_PATH]

PLOTS = False

# FIXME: Use proper fixtures and patching here, see ScopeSim test guide.


def test_eso_vs_scopesim_throughput():
    rc.__currsys__["!TEL.temperature"] = 7
    slist = sim.effects.SurfaceList(filename="LIST_mirrors_ELT.tbl")
    wave = np.linspace(0.3, 2.5, 100) * u.um
    if PLOTS:
        plt.plot(wave, slist.throughput(wave), label="ScopeSim")

    ter = sim.effects.TERCurve(filename="TER_ELT_5_mirror.dat")

    if PLOTS:
        plt.plot(wave, ter.surface.reflection(wave), label="ESO-253082")

        plt.legend(loc=4)
        plt.show()


## .todo: the values are not correct
@pytest.mark.xfail(reason="Does fail with ScopeSim 0.7.1. TODO: Remove mark when 0.8.0 is released.")
def test_eso_vs_scopesim_emission():
    cmds = UserCommands(properties={
        "!ATMO.temperature": 0.,
        "!TEL.temperature": "!ATMO.temperature",
        "!TEL.etendue": (1 * u.m * u.arcsec)**2,
    })

    slist = sim.effects.SurfaceList(filename="LIST_mirrors_ELT.tbl", cmds=cmds)
    ter = sim.effects.TERCurve(filename="TER_ELT_5_mirror.dat",
                               temperature="!ATMO.temperature",
                               cmds=cmds)

    wave = np.linspace(0.3, 12.5, 100) * u.um
    sl_flux = slist.emission(wave)
    ter_flux = ter.surface.emission(wave)

    if PLOTS:

        plt.plot(wave, sl_flux, label="ScopeSim")
        plt.plot(wave, ter_flux, label="ESO-253082")

        plt.semilogy()
        plt.legend(loc=2)
        plt.ylim(ymin=1e-10)
        plt.show()


@pytest.fixture(name="elt_configs", scope="class")
def fixture_elt_configs():
    """Instantiate ELT combined surface lists"""
    rc.__currsys__["!ATMO.temperature"] = 0.
    rc.__currsys__["!TEL.temperature"] = "!ATMO.temperature"
    rc.__currsys__["!TEL.etendue"] = (1 * u.m * u.arcsec)**2

    rc.__currsys__["!TEL.ter_curve.filename"] = "TER_ELT_5_mirror.dat"
    slist_5 = sim.effects.SurfaceList(filename="LIST_ELT_combined.tbl")

    rc.__currsys__["!TEL.ter_curve.filename"] =\
        "TER_ELT_6_mirror_pupil_track.dat"
    slist_6p = sim.effects.SurfaceList(filename="LIST_ELT_combined.tbl")

    rc.__currsys__["!TEL.ter_curve.filename"] = \
        "TER_ELT_6_mirror_field_track.dat"
    slist_6f = sim.effects.SurfaceList(filename="LIST_ELT_combined.tbl")

    return {'5 mirror': slist_5,
            '6 mirror pupil': slist_6p,
            '6 mirror field': slist_6f}


class TestELTConfigurations:
    refwave = 2. * u.um

    def test_5_mirror_emits_less_than_6_mirror(self, elt_configs):
        slist_5 = elt_configs['5 mirror']
        slist_6p = elt_configs['6 mirror pupil']
        assert (slist_5.emission(self.refwave)
                <
                slist_6p.emission(self.refwave))

    def test_pupil_track_emits_less_than_field_track(self, elt_configs):
        slist_6p = elt_configs['6 mirror pupil']
        slist_6f = elt_configs['6 mirror field']
        assert (slist_6p.emission(self.refwave)
                <
                slist_6f.emission(self.refwave))

    def test_5_mirror_absorbs_less_than_6_mirror(self, elt_configs):
        slist_5 = elt_configs['5 mirror']
        slist_6p = elt_configs['6 mirror pupil']
        assert (slist_5.throughput(self.refwave)
                >
                slist_6p.throughput(self.refwave))

    def test_pupil_track_absorbs_same_as_field_track(self, elt_configs):
        slist_6p = elt_configs['6 mirror pupil']
        slist_6f = elt_configs['6 mirror field']
        assert (slist_6p.throughput(self.refwave)
                ==
                slist_6f.throughput(self.refwave))
