# Step 3: Spectrograph throughput and IFU detectors

## Goal

Make IFU fluxes and noise quantitative, rather than optimistic. Applies to
both the cube modes of [step 1](step1_ifu_cube_mode.md) and the dispersed
modes of [step 2](step2_ifu_slicer_and_traces.md).

## Status: partly blocked

The throughput chain up to the spectrograph entrance already exists and is
validated. What is missing is everything downstream of the AO module, plus
the IFU detector characterisation.

## What already exists and is reused

The IFU sees the same front end as the imager, all of it already in the
package and cross-checked in the radiometry tests:

| Component | File | Provenance |
|---|---|---|
| Atmosphere | `Paranal.yaml` → skycalc | ESO service |
| Telescope | `VLT/LIST_VLT_mirrors.dat` | VLT user manual |
| AO module | `MAVIS/TER_aom_throughput.dat` | ~63 % at 550 nm, approximate |
| MCAO PSF | `MAVIS/PSF_MAVIS_mcao.fits` | MAVISIM e2e at 550 nm |

Note the AO module curve is itself only anchored on a single nominal value —
improving it benefits the imager too.

## What is missing

### 3.1 — Spectrograph optical throughput

Everything from the IFU pick-off to the detector: relay optics, slicer
mirrors, collimator, camera. Needed as a wavelength-resolved `TERCurve` or a
`SurfaceList` over the surfaces.

**Ask for:** the throughput budget per configuration, or the surface list with
coatings so a `SurfaceList` can be built the way `LIST_MAVIS_optics.dat` is.

**Interim option:** a flat throughput per configuration, clearly labelled an
estimate, so the cube modes are not silently missing a factor. A visible-light
slicer spectrograph plausibly lands in the 30–50 % range excluding grating
and detector, but **that is a guess and must be marked as one** — do not put
a number in without the `status : development` and "ESTIMATE" markers the
package uses elsewhere.

### 3.2 — Grating efficiency

One curve per spectral configuration. METIS models this with
`MetisLMSEfficiency`; a plain `TERCurve` per config is enough if the gratings
are not order-tunable.

**Ask for:** blaze wavelength, groove density, and measured or modelled
efficiency curves for the four configurations.

### 3.3 — IFU detector characterisation

The cube modes currently have to borrow the imager CCD's values, and those
are themselves partly estimates (`MAVIS/docs/README.md`, Known limitations).

**Ask for:** detector type and format, pixel pitch, QE curve, read noise per
readout mode, dark current, full well, gain, MINDIT, and linearity.

Until then, reusing `QE_mavis_ccd.dat`, `FPA_mavis_linearity.dat` and the
imager's noise values is defensible — the imager and IFU detectors are likely
similar-generation visible CCDs — but it must be stated in the YAML
`description` and in Known limitations.

## Validation targets, once data exists

Phase A quotes per-configuration limiting magnitudes, which are the natural
end-to-end check. Note these are **phase-A** numbers and the ESO baseline page
does not repeat them, so confirm before trusting them:

| Config | Limiting magnitude |
|---|---|
| LR-Blue | 21 at 550 nm |
| LR-Red | 21.5 at 750 nm |
| HR-Blue | 19.6 at 475 nm |
| HR-Red | 20.7 at 725 nm |

The exposure time, S/N and aperture these refer to are not stated on the
consortium page — get those too, otherwise the comparison is unanchored.
The imager equivalent (V > 29 at 5σ in 1 hr) is already used this way in
`TestRadiometry::test_point_source_sensitivity`, and that test's docstring
records the assumptions it had to make; do the same here.

## Suggested test structure

Follow the imager's pattern in `MAVIS/tests/test_mavis.py`:

- Validate the *bookkeeping* against a hand integration, which needs no
  consortium data and catches real bugs — this is how the imager sky level
  was pinned to 0.3 %.
- Validate the *performance* against published limiting magnitudes, with the
  assumptions written into the docstring.
- Record both in the generated report via the `report` fixture, so
  `MAVIS/docs/radiometry_report.md` carries the IFU numbers alongside the
  imager's.
