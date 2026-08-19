# MAVIS Radiometry Report

Auto-generated on **2026-08-19 16:36** by `pytest MAVIS/tests/`

MAVIS (MCAO Assisted Visible Imager and Spectrograph) is a next-generation ESO VLT instrument at the Nasmyth A focus of UT4 (Yepun). It uses an MCAO system to deliver near-diffraction-limited images in the visible over a 30x30 arcsec field of view.

Instrument parameters, the filter list and known limitations are documented in [README.md](README.md); the underlying specifications and their sources are in [../background_info/mavis_baseline_specification.md](../background_info/mavis_baseline_specification.md). This file holds only the numbers measured by the test suite.

**Note:** the PSF is an analytic MCAO model rather than an end-to-end simulation, and the filter curves are the standard passbands MAVIS is expected to carry rather than measured MAVIS hardware. This report is a consistency check, not a science-grade performance prediction.

## Validation against published numbers

| Quantity | Measured | Reference |
|---|---|---|
| Sky background, V band | 1314 e-/s/arcsec2 | 1316 e-/s/arcsec2, from integrating the skycalc emission spectrum through the system throughput by hand |
| Limiting magnitude, V band | 27.90 mag | > 29 mag published, at 5 sigma in 1 hr; measured in a 50 mas aperture |

The sky comparison is an end-to-end check of the photon bookkeeping: emission, collecting area, throughput, QE, integration time and gain, against the same quantities integrated directly.

The limiting magnitude is measured in a fixed 50 mas aperture, the box the ensquared-energy specification refers to. The published figure assumes optimal PSF-weighted extraction and dark time, whereas skycalc is queried with its default (not dark) moon and airglow settings, so the number here is expected to come out a magnitude or so brighter.

## System Throughput

![System throughput](throughput.png)

System throughput per filter (VLT mirrors + AO module + filter + detector QE, **no atmosphere**).

## Limiting Magnitudes

![Limiting magnitudes](limiting_magnitudes.png)

