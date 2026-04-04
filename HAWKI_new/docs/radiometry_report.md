# HAWKI_new Radiometry Report

Auto-generated on **2026-04-04 10:36** by `pytest HAWKI_new/tests/`

Source code: [test_hawki_new.py](../tests/test_hawki_new.py) | [conftest.py](../tests/conftest.py)

## ESO Reference Values

Reference: [ESO HAWK-I Overview](https://www.eso.org/sci/facilities/paranal/instruments/hawki/overview.html), [HAWK-I User Manual v116.2](https://www.eso.org/sci/facilities/paranal/instruments/hawki/doc.html)

### Instrument Parameters

| Parameter | Value |
|-----------|-------|
| Field of view | 7.5' x 7.5' |
| Pixel scale | 0.1064 arcsec/pixel |
| Detectors | 4x Hawaii-2RG (2048x2048) |
| Wavelength range | 0.9 - 2.5 um |
| Read noise (DIT > 15s) | ~5 e- |
| Dark current (75K) | 0.10 - 0.15 e-/s/pixel |
| Linear range | 60,000 e- |

### ESO Limiting Magnitudes

S/N = 5 on a point source, 3600s integration, 0.8" seeing, airmass 1.2:

| Filter | Limiting mag [Vega] | Limiting mag [AB] |
|--------|--------------------:|------------------:|
| J      |               23.9 |              24.8 |
| H      |               22.5 |              23.9 |
| Ks     |               22.3 |              24.2 |

*No radiometry data collected. Run slow tests with `pytest HAWKI_new/tests/ -m slow` to include radiometry tests.*
