"""
0-mag photon fluxes from Vega Spectrum
--------------------------------------
J band (J=0mag)   --> 3505e6 ph/s/m2
H band (H=0mag)   --> 2416e6 ph/s/m2
Ks band (Ks=0mag) --> 1211e6 ph/s/m2
Lp band (Lp=0mag) -->  576e6 ph/s/m2
Mp band (Mp=0mag) -->  268e6 ph/s/m2


SkyCalc Background levels mag/arcsec2
-------------------------------------
J:  16.87   --> 2e-7 * Vega = 0.7e3 ph/s/m2/arcsec2
H:  14.43   --> 2e-6 * Vega = 4.2e3 ph/s/m2/arcsec2
K:  15.23   --> 8e-7 * Vega = 1.0e3 ph/s/m2/arcsec2
L:   6.00   --> 0.04 * Vega = 2.3e6 ph/s/m2/arcsec2
M:   1.14   --> 0.35 * Vega = 94e6  ph/s/m2/arcsec2


NACO ETC
--------
NACO J Background: 123 e-/s/pixel   @ Sky BG J=14 mag
VLT area = 52m2
NACO pixels = 0.027"
[J Width = 0.25µm]
NACO J Sky Background (@ 14.0 mag) = 3.2e3 e-/s/m2/arcsec2    (incl. QE and TER)
NACO J Sky Background (@ 16.8 mag) = 0.3e3 e-/s/m2/arcsec2    (incl. QE and TER)

NACO Ks Background: 141 e-/s/pixel   @ Sky BG Ks=12.3 mag
VLT area = 52m2
NACO pixels = 0.027"
[Ks Width = 0.25µm]
NACO Ks Sky Background (@ 12.3 mag) = 3.7e3 e-/s/m2/arcsec2    (incl. QE and TER)
NACO Ks Sky Background (@ 15.2 mag) = 0.3e3 e-/s/m2/arcsec2    (incl. QE and TER)

NACO Lp Background: 291568 e-/s/pixel   @ Sky BG Lp=3 mag
NACO pixels = 0.027"
VLT area = 52m2
[Lp Width = 0.7µm]
NACO Lp Sky Background (@ 3 mag) = 7.7e6 e-/s/m2/arcsec2      (incl. QE and TER)
NACO Lp Sky Background (@ 6 mag) = 0.5e6 e-/s/m2/arcsec2      (incl. QE and TER)


ScopeSim using SkyCalc defaults
-------------------------------
J  BG: 688 ph/s/m2/arcsec2
H  BG: 4e3 ph/s/m2/arcsec2
Ks BG: 1e3 ph/s/m2/arcsec2
Lp BG: 4e6 ph/s/m2/arcsec2


Summary of ph/s/m2/arcsec2
--------------------------
NACO @ skycalc mags < Skycalc default mags == ScopeSim BG flux < NACO ETC mags

"""

import pytest
import numpy as np

from astropy import units as u
from matplotlib import pyplot as plt
import yaml

import scopesim as sim
from scopesim.source.source_templates import empty_sky, vega_spectrum

PLOTS = False

YAML_TEXT = """
alias: SIM
name: simulation_parameters

properties :
  spectral : 
    wave_min : %s
    wave_max : %s
    spectral_resolution : 0.005
    
  file:
    local_packages_path: "./"

--- 
alias: INST
name: basic_optical_system

properties :
  image_plane_id : 0
  pixel_scale : %s            # arcsec / pixel
  plate_scale : %s            # arcsec / mm

effects :
-   name : armazones_atmo_skycalc_ter_curve
    description : atmospheric spectra pulled from the skycalc server
    class : SkycalcTERCurve
    include : True
    kwargs :
        observatory : armazones
        wmin : "!SIM.spectral.wave_min"
        wmax : "!SIM.spectral.wave_max"
        wunit : um
        wdelta : "!SIM.spectral.spectral_resolution"

- name: filter TC
  class: SpanishVOFilterCurve
  kwargs:
    observatory: Paranal
    instrument: NACO
    filter_name: %s

- name: detector array list
  class: DetectorList
  kwargs:
    array_dict: {"id": [1], "x_cen": [0], "y_cen":[0], "x_size": [16],
                 "y_size": [16], "pixel_size": [1.], "angle": [0.], 
                 "gain": [1.0]}
    x_cen_unit : mm
    y_cen_unit : mm
    x_size_unit : mm
    y_size_unit : mm
    pixsize_unit : mm
    angle_unit : deg
    gain_unit : electron/adu
    
"""

wave_min = 1.8
wave_max = 2.4
filter_name = "Ks"
pixel_scale = 0.01


class TestArmazones:
    @pytest.mark.parametrize("pixel_scale", [1, 0.1, 10])
    def test_flux_scales_with_pixel_scale(self, pixel_scale):
        yaml_text = YAML_TEXT % (wave_min, wave_max, pixel_scale,
                                 pixel_scale, filter_name)
        yamls = [yml for yml in yaml.full_load_all(yaml_text)]

        cmd = sim.UserCommands(yamls=yamls)
        opt = sim.OpticalTrain(cmd)
        opt.cmds["!TEL.area"] = 1 * u.m**2

        src = empty_sky()
        opt.observe(src)
        img = opt.image_planes[0].data

        # Ks band photon flux is 1014 ph/s/m2/arcsec2
        assert np.median(img) == pytest.approx(1014 * pixel_scale**2, rel=0.01)

        if PLOTS:
            plt.imshow(img)
            plt.show()

    def photons_in_vega_spectrum(self):
        for filter_name in ["J", "H", "Ks", "Lp", "Mp"]:
            vega = vega_spectrum()
            kwargs = {"observatory": "Paranal", "instrument": "NACO",
                      "filter_name": filter_name}
            filt = sim.effects.SpanishVOFilterCurve(**kwargs)
            wave = filt.surface.table["wavelength"]
            trans = filt.surface.table["transmission"]
            dwave = 0.5 * (np.r_[[0], np.diff(wave)] +
                           np.r_[np.diff(wave), [0]]) * u.AA

            flux = vega(wave)                   # ph/s/cm2/AA
            flux *= trans * dwave    # ph/s
            sum_flux = np.sum(flux.to(u.ph/u.s/u.m**2).value)

            print(f"\nVega spectrum over the {filter_name} band "
                  f"({filter_name}=0mag) has a flux of "
                  f"{int(sum_flux*1e-6)}e6 ph/s/m2")
