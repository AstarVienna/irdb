"""Tests for ELT vs. WCU modes

These tests check that the yamls for the ELT/Armazones and METIS_WCU are loaded for the
modes where they belong (and not loaded where they do not belong). This is done by
checking the "elements" in the effects list of the OpticalTrain objects.
"""
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import pytest

import scopesim
PKGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
scopesim.rc.__config__["!SIM.file.local_packages_path"] = PKGS_DIR

ELT_MODES = ["img_lm", "img_n", "lss_l", "lss_m", "lss_n", "lms", "lms_extended"]
# Generate WCU_MODES automatically to ensure that each elt mode has a corresponding wcu mode
WCU_MODES = [("wcu_" + mode) for mode in ELT_MODES]

class TestModes:
    @pytest.mark.parametrize("themode", ELT_MODES)
    def test_elt_modes_include_elt_effects(self, themode):
        cmd = scopesim.UserCommands(use_instrument="METIS",
                                    set_modes=[themode])
        metis = scopesim.OpticalTrain(cmd)
        assert "ELT" in metis.effects["element"]
        assert "armazones" in metis.effects["element"]
        assert "METIS_WCU" not in metis.effects["element"]

    @pytest.mark.parametrize("themode", WCU_MODES)
    def test_wcu_modes_include_wcu_effects(self, themode):
        cmd = scopesim.UserCommands(use_instrument="METIS",
                                    set_modes=[themode])
        metis = scopesim.OpticalTrain(cmd)
        assert "ELT" not in metis.effects["element"]
        assert "armazones" not in metis.effects["element"]
        assert "METIS_WCU" in metis.effects["element"]
