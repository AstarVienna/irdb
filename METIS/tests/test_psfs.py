"""Tests PSFs in WCU modes

These tests check that the OpticalTrains have the correct PSFs
for the default pupil masks in the WCU modes
"""
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import pytest

import scopesim
PKGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
scopesim.rc.__config__["!SIM.file.local_packages_path"] = PKGS_DIR

class TestModes:
    @pytest.mark.parametrize("themode, themask",
                             [("wcu_img_lm", "PPS-LM"),
                              ("wcu_img_n", "PPS-N"),
                              ("wcu_lss_l", "PPS-CFO2"),
                              ("wcu_lss_m", "PPS-CFO2"),
                              ("wcu_lss_n", "PPS-CFO2"),
                              ("wcu_lms", "PPS-LMS")])
    def test_wcu_modes_use_correct_default_psf(self, themode, themask):
        cmd = scopesim.UserCommands(use_instrument="METIS",
                                    set_modes=[themode])
        metis = scopesim.OpticalTrain(cmd)
        assert metis['psf'].meta['psf_name'] == themask
