"""
Tests that the MICADO package runs with observe, readout flawlessly

Comments
--------
- 2022-03-18 (KL) Green locally
  ! SPEC mode is missing from the tests.

.. todo:: Add SPEC modes to these tests

"""

# integration test using everything and the MICADO package
from pathlib import Path
import pytest
from pytest import approx
import os

import numpy as np
from astropy.io import fits

import scopesim
from scopesim import rc

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

PATH_HERE = Path(__file__).parent
PATH_IRDB = PATH_HERE.parent.parent

rc.__config__["!SIM.file.local_packages_path"] = str(PATH_IRDB)
PLOTS = False


class TestInit:
    def test_all_packages_are_available(self):
        rc_local_path = rc.__config__["!SIM.file.local_packages_path"]
        for pkg_name in ["Armazones", "ELT", "MORFEO", "MICADO"]:
            assert os.path.isdir(os.path.join(rc_local_path, pkg_name))


class TestLoadUserCommands:
    def test_user_commands_loads_without_throwing_errors(self, capsys):
        cmd = scopesim.UserCommands(use_instrument="MICADO")
        assert isinstance(cmd, scopesim.UserCommands)
        for key in ["SIM", "OBS", "ATMO", "TEL", "INST", "DET"]:
            assert key in cmd and len(cmd[key]) > 0
        stdout = capsys.readouterr()

        assert len(stdout.out) == 0

    def test_user_commands_loads_mode_files(self):
        cmd = scopesim.UserCommands(use_instrument="MICADO")
        yaml_names = [yd["name"] for yd in cmd.yaml_dicts]

        assert "MICADO_IMG_LR" in yaml_names

    def test_user_commands_can_change_modes(self):
        cmd = scopesim.UserCommands(use_instrument="MICADO")
        cmd.set_modes(["MCAO", "SPEC_3000x50"])

        assert "MORFEO" in [yd["name"] for yd in cmd.yaml_dicts]
        assert "MICADO_SPEC" in [yd["name"] for yd in cmd.yaml_dicts]

    def test_user_commands_can_change_modes_via_init(self):
        cmd = scopesim.UserCommands(use_instrument="MICADO",
                                    set_modes=["MCAO", "SPEC_3000x50"])

        assert "MORFEO" in [yd["name"] for yd in cmd.yaml_dicts]
        assert "MICADO_SPEC" in [yd["name"] for yd in cmd.yaml_dicts]


class TestMakeOpticalTrain:
    def test_works_seamlessly_for_micado_wide_mode(self):
        cmd = scopesim.UserCommands(use_instrument="MICADO",
                                    set_modes=["SCAO", "IMG_4mas"],
                                    properties={"!OBS.filter_name": "Ks"})
        opt = scopesim.OpticalTrain(cmd)
        assert isinstance(opt, scopesim.OpticalTrain)

        src = scopesim.source.source_templates.empty_sky()
        opt.observe(src)
        hdu_list = opt.readout()[0]

        assert isinstance(hdu_list, fits.HDUList)

    def test_works_seamlessly_for_micado_zoom_mode(self):
        cmd = scopesim.UserCommands(use_instrument="MICADO",
                                    set_modes=["SCAO", "IMG_1.5mas"],
                                    properties={"!OBS.filter_name_fw1": "J",
                                                "!OBS.filter_name_fw2": "open"})
        micado = scopesim.OpticalTrain(cmd)
        assert isinstance(micado, scopesim.OpticalTrain)

        src = scopesim.source.source_templates.empty_sky()
        micado.observe(src)
        hdu_list = micado.readout()[0]

        assert isinstance(hdu_list, fits.HDUList)


class TestDetector:
    @pytest.mark.parametrize("ndit, dit", [(1, 3600)])
    def test_returns_ndit_dit_scaled_image(self, ndit, dit):
        cmd = scopesim.UserCommands(use_instrument="MICADO",
                                    properties={"!OBS.dit": dit,
                                                "!OBS.ndit": ndit})
        micado = scopesim.OpticalTrain(cmd)
        micado["skycalc_atmosphere"].include = False
        micado["detector_linearity"].include = False

        src = scopesim.source.source_templates.empty_sky()
        micado.observe(src)
        implane_image = micado.image_planes[0].data

        hdus = micado.readout()
        readout_image = hdus[0][1].data

        imp_av = np.median(implane_image) * ndit * dit
        hdu_av = np.median(readout_image)

        if PLOTS:
            plt.subplot(121)
            plt.imshow(implane_image, norm=LogNorm())
            plt.colorbar()

            plt.subplot(122)
            plt.imshow(readout_image, norm=LogNorm())
            plt.colorbar()

            plt.show()

        assert imp_av == approx(hdu_av, rel=0.05)
