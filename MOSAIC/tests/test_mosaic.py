"""Basic unit tests for irdb/MOSAIC"""
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
from glob import glob

import pytest

import numpy as np
#from astropy.io.fits import HDUList
from astropy import units as u
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

import scopesim
from scopesim.source.source_templates import star_field
#import scopesim_templates as sim_tp

PLOTS = False
PKGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
scopesim.rc.__config__["!SIM.file.local_packages_path"] = PKGS_DIR


class TestLoads:
    """Test that irdb/MOSAIC is loaded and an OpticalTrain is produced"""

    @pytest.mark.parametrize("themode",
                            ["MOS-LR-B", "MOS-HR-B1", "MOS-HR-B2", "MOS-LR-R",
                             "MOS-HR-R1", "MOS-HR-R2", "MOS-LR-J", "MOS-LR-H",
                             "MOS-HR-H", "mIFU-LR-J", "mIFU-LR-H", "mIFU-HR-H"])
    def test_scopesim_loads_package(self, themode):
        """Load the configuration for all supported modes"""
        cmd = scopesim.UserCommands(use_instrument="MOSAIC",
                                    set_modes=[themode])
        assert isinstance(cmd, scopesim.UserCommands)

        mosaic = scopesim.OpticalTrain(cmd)
        assert isinstance(mosaic, scopesim.OpticalTrain)


YAML_LIST = glob(os.path.join(PKGS_DIR, "MOSAIC/*.yaml"))
@pytest.fixture(name="yaml_list", scope="class", params=YAML_LIST)
def fixture_yaml_list(request):
    return scopesim.commands.user_commands.load_yaml_dicts(request.param)

class TestYAML:
    """Test that yaml files result in correct lists"""

    def test_yaml_read_okay(self, yaml_list):
        """yaml file is read correctly and gives list"""
        assert isinstance(yaml_list, list)

    def test_yaml_length_not_zero(self, yaml_list):
        """yaml_list has entries"""
        assert len(yaml_list) > 0

    def test_yaml_entries_are_dicts(self, yaml_list):
        """yaml list entries are dictionaries"""
        for yaml_entry in yaml_list:
            assert isinstance(yaml_entry, dict)


QE_LIST = glob(os.path.join(PKGS_DIR, "MOSAIC/QE_detector_*.dat"))
@pytest.fixture(name="qe_curve", scope="class", params=QE_LIST)
def fixture_qe_curve(request):
    return scopesim.effects.QuantumEfficiencyCurve(filename=request.param)

class TestQuantumEfficiency:
    """Test that QE files result in correct QuantumEfficiencyCurves"""

    def test_qe_read_okay(self, qe_curve):
        """qe file is read correctly and gives QuantumEfficiencyCurve"""
        assert isinstance(qe_curve, scopesim.effects.QuantumEfficiencyCurve)

    def test_qe_table_not_zero(self, qe_curve):
        """Table attribute shall not be empty"""
        assert len(qe_curve.table) > 0

    def test_qe_has_wavelength_unit(self, qe_curve):
        """qe file specifies a wavelength unit"""
        assert 'wavelength_unit' in qe_curve.meta

    def test_qe_wavelength_parses_correctly(self, qe_curve):
        """wavelength unit is parsed by astropy.units"""
        wunit = qe_curve.meta['wavelength_unit']
        assert isinstance(u.Unit(wunit), u.Unit)


TER_LIST = glob(os.path.join(PKGS_DIR, "METIS/TER_*.dat"))
@pytest.fixture(name="ter_curve", scope="class", params=TER_LIST)
def fixture_ter_curve(request):
    return scopesim.effects.TERCurve(filename=request.param)

class TestTERCurve:
    """Test that TER files result in correct TERCurves"""

    def test_ter_read_okay(self, ter_curve):
        """ter file is read correctly and gives TERCurve"""
        assert isinstance(ter_curve, scopesim.effects.TERCurve)

    def test_ter_table_not_zero(self, ter_curve):
        """Table attribute shall not be empty"""
        assert len(ter_curve.table) > 0

    def test_ter_has_wavelength_unit(self, ter_curve):
        """ter file specifies a wavelength unit"""
        assert 'wavelength_unit' in ter_curve.meta

    def test_ter_wavelength_parses_correctly(self, ter_curve):
        """wavelength unit is parsed by astropy.units"""
        wunit = ter_curve.meta['wavelength_unit']
        assert isinstance(u.Unit(wunit), u.Unit)


FPA_LIST = glob(os.path.join(PKGS_DIR, "MOSAIC/FPA_*_layout.dat"))
@pytest.fixture(name="det_list", scope="class", params=FPA_LIST)
def fixture_det_list(request):
    return scopesim.effects.DetectorList(filename=request.param)

class TestFPALayout:
    """Test that FPA files result in correct DetectorLists"""
    # Do we need explicit tests for units?
    def test_fpa_read_okay(self, det_list):
        """fpa layout is read correctly and gives DetectorList"""
        assert isinstance(det_list, scopesim.effects.DetectorList)

    def test_fpa_table_not_zero(self, det_list):
        """Table attribute shall not be empty"""
        assert len(det_list.table) > 0


LIN_LIST = glob(os.path.join(PKGS_DIR, "MOSAIC/FPA_linearity_*.dat"))
@pytest.fixture(name="lin_curve", scope="class", params=LIN_LIST)
def fixture_lin_curve(request):
    return scopesim.effects.LinearityCurve(filename=request.param)

class TestLinearityCurve:
    """Test that linearity files result in correct LinearityCurves"""

    def test_lin_read_okay(self, lin_curve):
        """linearity curve is read correctly and gives LinearityCurve"""
        assert isinstance(lin_curve, scopesim.effects.LinearityCurve)

    def test_lin_table_not_zero(self, lin_curve):
        """Table attribute shall not be empty"""
        assert len(lin_curve.table) > 0


TRACE_LIST = glob(os.path.join(PKGS_DIR, "MOSAIC/TRACE*.fits"))
@pytest.fixture(name="trace_list", scope="class", params=TRACE_LIST)
def fixture_trace_list(request):
    return scopesim.effects.MosaicSpectralTraceList(filename=request.param)

class TestTraceFile:
    """Test that trace files result in correct MosaicSpectralTraces
    """

    def test_tracelist_read_okay(self, trace_list):
        """Trace file is read correctly and gives SpectralTrace"""
        assert isinstance(trace_list, scopesim.effects.MosaicSpectralTraceList)

    def test_tracelist_has_table(self, trace_list):
        """Trace list has a table with at least one entry"""
        assert len(trace_list.data) > 0

    def test_tracelist_has_traces(self, trace_list):
        """SpectralTraceList contains at least one SpectralTrace"""
        for trace in trace_list.spectral_traces:
            assert isinstance(trace_list.spectral_traces[trace],
                              scopesim.effects.SpectralTrace)


@pytest.mark.slow
class TestObserves:
    """Test basic observations for the main instrument modes"""
    def test_something_comes_out_mos_lr_r(self):
        """Basic test for MOS-LR-R"""
        src = star_field(100, 0, 10, width=10, use_grid=True)
        # convert to single star

        cmds = scopesim.UserCommands(use_instrument="MOSAIC",
                                     set_modes=['MOS-LR-R'])
        mosaic = scopesim.OpticalTrain(cmds)
        #mosaic['detector_linearity'].include = False

        mosaic.observe(src)
        hdus = mosaic.readout()

        im = mosaic.image_planes[0].data
        mx, med, std = np.max(im), np.median(im), np.std(im)

        if PLOTS:
            for i, img in enumerate([mosaic.image_planes[0].data,
                                     hdus[0][1].data]):
                plt.subplot(1, 2, i+1)
                med = np.median(img)
                plt.imshow(img, norm=LogNorm(), vmin=0.7*med, vmax=1.3*med)
                plt.title("MOS-LR-R Test")
                plt.colorbar()
            plt.show()

        assert mx > med + 3 * std

    def test_something_comes_out_mifu_lr_h(self):
        """Basic test for mIFU-LR-H"""
        src = star_field(100, 0, 10, width=10, use_grid=True)

        cmds = scopesim.UserCommands(use_instrument="MOSAIC",
                                     set_modes=["mIFU-LR-H"])

        mosaic = scopesim.OpticalTrain(cmds)
        #mosaic['detector_linearity'].include = False

        mosaic.observe(src)
        hdus = mosaic.readout()

        im = mosaic.image_planes[0].data
        mx, med, std = np.max(im), np.median(im), np.std(im)

        if PLOTS:
            for i, img in enumerate([mosaic.image_planes[0].data,
                                     hdus[0][1].data]):
                plt.subplot(1, 2, i+1)
                med = np.median(img)
                plt.imshow(img, vmin=0.7*med, vmax=1.3*med, norm=LogNorm())
                plt.title("mIFU-LR-H Test")
                plt.colorbar()
            plt.show()

        assert mx > med + 3 * std

        # This should not be here, but putting it into a separate test would work
        # better if the simulation were done in a fixture
        assert isinstance(hdus[0][1].header["INHERIT"], bool)
