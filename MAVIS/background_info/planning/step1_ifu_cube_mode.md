# Step 1: IFU cube modes

## Goal

Give MAVIS working IFU modes that output a **datacube** (x, y, λ) rather than
a dispersed detector image, using ScopeSim's simple-IFU path. This delivers a
usable ETC-grade spectrograph without inventing any of the spectrograph
optics.

## Why this is not blocked

The dispersed-image path needs the slicer geometry, the trace mapping and the
detector layout, none of which are published (see
[step2](step2_ifu_slicer_and_traces.md)). The cube path does not. Everything
it needs is either published or a standard, statable sampling convention:

| Cube mode needs | Where it comes from | Invented? |
|---|---|---|
| Spatial extent | Published IFU FoV | No |
| Spatial sampling | Published spaxel scale | No |
| Wavelength range | Published per spectral config | No |
| Spectral sampling | 2 pixels per resolution element | **Convention**, stated |
| LSF width | 2 cube bins, follows from the above | **Convention**, stated |
| Detector noise | Not published | **Yes** — see below |

Only the last row is a real gap, and it can be deferred: the cube modes are
useful for throughput, resolution and cube-geometry work before the noise
model is right.

## ScopeSim precedent

METIS `IFU_SMPL` (added in ScopeSim 0.10.0) is the reference implementation:

- `METIS/METIS_LMS_SMPL.yaml` — `LineSpreadFunction` + `FluxBinning3D`,
  with `flatten: False` and `decouple_detector_from_sky_headers: True`
- `METIS/METIS_DET_IFU_SMPL.yaml` — `DetectorList3D`
- `METIS/FPA_metis_lms_smpl_layout.dat` — a **single-row** layout giving
  `x_size`, `y_size` in spatial pixels and `z_size` in spectral pixels

Effects live in `scopesim/effects/metis_ifu_simple/`.

## Parameters

### Spectral configurations

From the ESO baseline. `N_resel = R ln(λ_max/λ_min)`; `z_size` assumes
2 pixels per resolution element.

| Config | R | Range [µm] | N_resel | z_size [pix] | Δλ at band centre [µm] |
|---|---|---|---|---|---|
| LR-Blue | 5 900 | 0.370–0.720 | 3 928 | 7 856 | 4.62e-5 |
| LR-Red | 5 900 | 0.510–0.935 | 3 576 | 7 152 | 6.12e-5 |
| HR-Blue | 14 700 | 0.425–0.550 | 3 790 | 7 580 | 1.66e-5 |
| HR-Red | 11 500 | 0.630–0.880 | 3 843 | 7 687 | 3.28e-5 |

```{note}
Phase A quotes a slightly different LR-Red range (510–1000 nm) and adds
per-config limiting magnitudes. The ESO baseline is used above. See
`../mavis_baseline_specification.md`.
```

### Spatial scales

The published spaxel sizes are ranges, not single values, because the design
was not frozen. Both ends are tabulated; pick one per mode and record which.

| Scale | Spaxel | FoV | Spaxels |
|---|---|---|---|
| fine | 20 mas | 2.5″ × 3.6″ | 125 × 180 |
| fine | 25 mas | 2.5″ × 3.6″ | 100 × 144 |
| coarse | 40 mas | 5″ × 7.2″ | 125 × 180 |
| coarse | 50 mas | 5″ × 7.2″ | 100 × 144 |

**Recommendation:** adopt 25 mas and 50 mas, the coarse end of each range.
They give the smaller cubes, they are the conservative choice for
sensitivity estimates, and 2 × 25 = 50 keeps the two scales in a clean ratio.

### Cube sizes — the practical problem

Full field × full band, float32:

| Config | 25/50 mas (100×144) | 20/40 mas (125×180) |
|---|---|---|
| LR-Blue | 0.42 GiB | 0.66 GiB |
| LR-Red | 0.38 GiB | 0.60 GiB |
| HR-Blue | 0.41 GiB | 0.64 GiB |
| HR-Red | 0.41 GiB | 0.64 GiB |

Half a gigabyte per readout is not an acceptable default, and ScopeSim holds
several intermediate cubes at once.

**Mitigation, in order of preference:**

1. Default to a **wavelength sub-band** rather than the full config range —
   e.g. 20 nm around a user-set `!OBS.wavelen`, mirroring how METIS LMS
   works (it also has a tunable central wavelength). This is likely to be
   physically correct as well: see the open question below.
2. Default to a **sub-field** (e.g. 1″ × 1″) with the full field opt-in.
3. Document the memory cost and let the user choose.

## Tasks

### 1.1 — Decide the spectral sampling convention

2 pixels per resolution element is the Nyquist standard and is what the table
above assumes. Record the choice in the YAML `description` so it is not
mistaken for a measured number.

### 1.2 — Resolve the simultaneous-vs-tunable question

**This is the one open question that materially changes the design.**

R = 5 900 over 370–720 nm needs ~3 900 resolution elements, i.e. ~7 900
detector pixels along dispersion. That does not fit on one 4k detector, so
either the spectrograph is a multi-detector mosaic (MUSE-like) or the quoted
range is a *tuning* range with a narrower simultaneous window.

- If **simultaneous**: `z_size` is the full number above and mitigation 2 or
  3 applies.
- If **tunable**: add a `!OBS.wavelen` property, and `z_size` becomes the
  simultaneous window only — much smaller cubes, and mitigation 1 is the
  natural design.

Until this is settled, implement the tunable form with the window as a
declared parameter, defaulting to the full range. It degrades gracefully
either way.

### 1.3 — Files to create

- `MAVIS_IFU.yaml` — common IFU optics: `alias: INST`, spaxel scale,
  `flatten: False`, `decouple_detector_from_sky_headers: True`,
  the AO module `SurfaceList` (shared with the imager), the MCAO PSF, and
  `LineSpreadFunction` with `lsfwidth: 2` (cube bins).
- `MAVIS_IFU_LR_BLUE.yaml`, `..._LR_RED.yaml`, `..._HR_BLUE.yaml`,
  `..._HR_RED.yaml` — one per spectral config, each setting the wavelength
  range, R, and the grating efficiency curve once step 3 supplies one.
- `MAVIS_IFU_DET.yaml` — `DetectorList3D`, `QuantumEfficiencyCurve`,
  `ExposureIntegration`, `ExposureOutput` (`mode: sum`), `ShotNoise`,
  `BasicReadoutNoise`, `DarkCurrent`, `ADConversion`.
  Mirror `MAVIS_CCD.yaml`; note the `ExposureIntegration` trap recorded
  there.
- `FPA_mavis_ifu_fine_layout.dat`, `FPA_mavis_ifu_coarse_layout.dat` —
  single-row `DetectorList3D` layouts. Copy the header block from
  `METIS/FPA_metis_lms_smpl_layout.dat`; `z_size` from the table above.
- `default.yaml` — add the modes under `mode_yamls`. **Do not repeat any
  yaml already in the base `yamls` list**: that duplicates every optical
  element and squares the throughput. There is a regression test for it
  (`TestRadiometry::test_effects_are_not_applied_twice`).

### 1.4 — SIM properties

The cube modes need a `spectral_bin_width` matched to the config, as METIS
does in a second YAML document of the mode file. Use the band-centre Δλ from
the table.

### 1.5 — Verification

- Cube axes: `NAXIS1/2` match the spaxel counts, `NAXIS3` matches `z_size`,
  and the WCS wavelength axis spans the published range.
- Spectral resolution: simulate a narrow emission line and recover
  R = λ/FWHM within a few per cent of the published value, per config.
- Spatial: the PSF in a monochromatic cube plane has the same FWHM as in the
  imager at that wavelength.
- Flux: a flat continuum source at known magnitude gives a cube whose
  wavelength-integrated flux matches an imager simulation through a filter
  covering the same range, to within the throughput difference. This is the
  same closure check the imager passes against skycalc.
- Sky: the skycalc emission spectrum appears in the cube at the right
  wavelengths and with the right line ratios.

## ScopeSim effects used

All exist; no ScopeSim changes needed.

| Effect | Purpose |
|---|---|
| `LineSpreadFunction` | Spectral resolution, `lsfwidth` in cube bins |
| `FluxBinning3D` | Converts per-arcsec per-µm to photons per second |
| `DetectorList3D` | Cube sampling grid |
| `SurfaceList` | AO module + spectrograph optics throughput |
| `FieldConstantPSF` | The MCAO PSF, shared with the imager |
| `QuantumEfficiencyCurve`, `ExposureIntegration`, `ExposureOutput`, `ShotNoise`, `BasicReadoutNoise`, `DarkCurrent`, `ADConversion` | Detector chain, as in `MAVIS_CCD.yaml` |

## What stays wrong after this step

- Spectrograph throughput and grating efficiency are missing, so absolute
  fluxes are optimistic by whatever the spectrograph costs (step 3).
- IFU detector noise is the imager CCD's, which is a guess (step 3).
- No dispersed-image output, so nothing about slice geometry, inter-slice
  gaps, or detector-level artefacts is modelled (step 2).
- The PSF is the imager's on-axis MCAO PSF. The IFU field is much smaller
  than the imager's, so field constancy is a better approximation here than
  it is for the imager — but it is still an approximation.
