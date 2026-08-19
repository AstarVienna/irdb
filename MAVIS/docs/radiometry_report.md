# MAVIS Radiometry Report

Auto-generated on **2026-08-19 15:57** by `pytest MAVIS/tests/`

MAVIS (MCAO Assisted Visible Imager and Spectrograph) is a next-generation ESO VLT instrument at the Nasmyth A focus of UT4 (Yepun). It uses an MCAO system to deliver near-diffraction-limited images in the visible over a 30x30 arcsec field of view.

Instrument parameters, the filter list and known limitations are documented in [README.md](README.md); the underlying specifications and their sources are in [../background_info/mavis_baseline_specification.md](../background_info/mavis_baseline_specification.md). This file holds only the numbers measured by the test suite.

**Note:** the PSF in this package is a placeholder Gaussian and the filter curves are top-hat approximations. This report is a consistency check, not a science-grade performance prediction.

## System Throughput

![System throughput](throughput.png)

System throughput per filter (VLT mirrors + AO module + filter + detector QE, **no atmosphere**).

