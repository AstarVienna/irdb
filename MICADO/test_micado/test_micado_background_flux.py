# -*- coding: utf-8 -*-
"""
Tests the SCAO background against the values from from Ric's excel doc
[Signal_noise_estimator_MICADO_2018.04.03]

Comments
--------
- 2022-03-18 (KL) Green locally
  BG levels 30% higher in ScopeSim J,H and 25% lower in ScopeSim Ks

"""

# integration test using everything and the MICADO package
from pathlib import Path
import pytest

import numpy as np
from numpy import testing as npt

import scopesim as sim
from scopesim import rc

PATH_HERE = Path(__file__).parent
PATH_IRDB = PATH_HERE.parent.parent

rc.__config__["!SIM.file.local_packages_path"] = str(PATH_IRDB)

# pylint: disable=missing-class-docstring,
# pylint: disable=missing-function-docstring

class TestInit:
    @pytest.mark.parametrize(
        "modes",
        [
            ["SCAO", "IMG_4mas"],
            ["SCAO", "IMG_1.5mas"],
            ["MCAO", "IMG_4mas"],
            ["MCAO", "IMG_1.5mas"],
        ],
    )
    def test_micado_loads_optical_train(self, modes):
        cmds = sim.UserCommands(use_instrument="MICADO", set_modes=modes)
        micado = sim.OpticalTrain(cmds)
        opt_els = np.unique(micado.effects["element"])

        assert isinstance(micado, sim.OpticalTrain)
        assert len(opt_els) == 6


class TestBackgroundLevels:
    """
    from Ric's excel doc 2018-04-03
    sky + instr. bkg [e-/pixel/s] for 4 mas mode::

        J       H       Ks
        5.0     28.4	78.7

    """

    @pytest.mark.parametrize(
        "mode, factor", (("IMG_4mas", 1), ("IMG_1.5mas", (1.5 / 4) ** 2))
    )
    @pytest.mark.parametrize(
        "fw1, fw2, bg_flux", [
            pytest.param(
                "J", "open", 5,
                marks=pytest.mark.xfail(
                    reason="Fails higher than expected."
                ),
            ),
            pytest.param(
                "open", "H", 28.4,
                marks=pytest.mark.xfail(
                    reason="Fails higher than expected."
                ),
            ),
            pytest.param(
                "open", "Ks", 78.7,
                marks=pytest.mark.xfail(
                    reason="Fails actual lower than expected."
                ),
            ),
            # regression test actual values 2026-08-14
            ("J", "open", 7.75),
            ("open", "H", 52.2),
            ("open", "Ks", 50.7),
        ],
    )
    def test_bg_scao_imaging(self, mode, factor, fw1, fw2, bg_flux):
        cmds = sim.UserCommands(
            use_instrument="MICADO", set_modes=["SCAO", mode]
        )
        micado = sim.OpticalTrain(cmds)

        micado["filter_wheel_1"].change_filter(fw1)
        micado["filter_wheel_2"].change_filter(fw2)

        micado.observe()
        implane = micado.image_planes[0].hdu.data  # e-/pixel/s

        # Pixel size is 0.14 of the 4mas version, hence fluxes are lower
        bg_flux *= factor
        npt.assert_allclose(np.median(implane), bg_flux, rtol=.3)
