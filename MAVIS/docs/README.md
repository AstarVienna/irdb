# MAVIS + ScopeSim

## Introduction

MAVIS (**M**CAO **A**ssisted **V**isible **I**mager and **S**pectrograph) is a
next-generation instrument for the VLT UT4 (Yepun) at the Nasmyth A focus, on
the Adaptive Optics Facility. MAVIS uses a Multi-Conjugate Adaptive Optics
(MCAO) system to deliver near-diffraction-limited images in the *visible* over
a 30″ × 30″ field of view. First light at the telescope is currently scheduled
for 2031.

The package implements the **imager** and **cube-output IFU modes**. The IFU
modes produce a datacube rather than a dispersed detector frame, because the
spectrograph's optical layout is unpublished — see
[IFU spectrograph](#ifu-spectrograph) below and the
[implementation plan](../background_info/planning/README.md).

```{warning}
**This package is under development and is not yet science-grade.**

Several of its data files are placeholders or approximations — most
importantly the PSF, the filter curves, and the AO module throughput. See
[Known limitations](#known-limitations) below before drawing quantitative
conclusions from a MAVIS simulation.
```

```{note}
**Bug reports and help desk**

If you come across a bug or get stuck with ScopeSim or the MAVIS package,
please [open an issue on GitHub](https://github.com/AstarVienna/irdb/issues)
or contact us by email (see below).

**Your feedback is the only way we know** what needs to be
changed or improved with the package and the simulator.

Please always include the output of `scopesim.bug_report()` from your
installation.
```

## Downloading the MAVIS instrument package

Once ScopeSim is installed, download the MAVIS instrument package into your
working directory:

```python
import scopesim
scopesim.download_packages(["Paranal", "VLT", "MAVIS"])
```

This installs the packages into the subdirectory `./inst_pkgs/`.

Your working directory should look like this afterwards:

```
my_simulations/
├── <your notebook>.ipynb
└── inst_pkgs/
    ├── Paranal/
    ├── VLT/
    └── MAVIS/
```

```{include} ../../docs/ScopeSim_guide.md
```

## Quick start

```python
import scopesim

cmd = scopesim.UserCommands(use_instrument="MAVIS",
                            properties={"!OBS.filter_name": "V",
                                        "!OBS.dit": 60,
                                        "!OBS.ndit": 1})
mavis = scopesim.OpticalTrain(cmd)
mavis.observe(src)
hdus = mavis.readout()
```

## AO system

| Property | Value |
|---|---|
| Type | MCAO (Multi-Conjugate AO) |
| Laser guide stars | up to 8, on a 17.5″ diameter circle |
| Natural guide stars | up to 3 (tip-tilt), over a 120″ diameter field |
| Deformable mirrors | AOF deformable secondary plus post-focal DMs |
| Wavelength correction range | 370–1000 nm |
| Strehl at 550 nm | > 8 % (goal 12 %) |
| Ensquared energy | > 15 % within 50 mas at 550 nm |
| Angular resolution | down to ~18 mas |
| Sky coverage | ⩾ 50 % at the South Galactic Pole |

```{note}
The publicly released MCAO PSF simulations (LAM, and MAVISIM) were generated
for a **5 LGS + 3 DM** configuration, which is *not* the current instrument
baseline of up to 8 LGS. State the configuration whenever you quote a PSF.
```

## Imager parameters

| Parameter | Value |
|---|---|
| Pixel scale | 7.36 mas/pixel |
| Field of view | 30″ × 30″ |
| Detector | Back-illuminated CCD, 4096 × 4004 |
| Pixel pitch | 10 µm |
| Wavelength range | 370–1000 nm (package models 320–1000 nm) |
| Read noise (slow mode) | 3 e⁻ |
| Read noise (fast mode) | 5 e⁻ |
| Full well capacity | 90 000 e⁻ |
| Gain | 1.0 ADU/e⁻ |
| QE at 550 nm | 89 % |
| AO module throughput | ~63 % at 550 nm |
| PSF FWHM (design, 550 nm) | ~10 mas |
| Sky background (V band) | 21.61 mag/arcsec² |
| Point-source sensitivity | V > 29 mag (5σ) in 1 hr |

## Available filters

Broadband (SDSS) — this is the set on the current ESO baseline:

- **u** — SDSS u′ (~315–395 nm)
- **g** — SDSS g′ (~400–555 nm)
- **r_SDSS** — SDSS r′ (~560–705 nm)
- **i_SDSS** — SDSS i′ (~690–835 nm)
- **z** — SDSS z′ (~835–1000 nm, limited by CCD QE)

Broadband (Bessel/Cousins) — from the phase-A filter list, kept as a convenience:

- **B** — Bessel B (~390–510 nm)
- **V** — Bessel V (centre 550 nm, FWHM 88 nm)
- **R** — Cousins R (~580–730 nm)
- **I** — Cousins I (~730–910 nm)

```{note}
SDSS r and i are named `r_SDSS` and `i_SDSS` (not `r`/`i`) to avoid a
filesystem case-collision with Cousins R and I on case-insensitive systems.
```

Narrow-band filters are part of the instrument baseline but are not yet in
this package.

## Detector readout modes

Selected via `!OBS.detector_readout_mode`:

| Mode | Read noise | Full well | Gain | Dark current |
|---|---|---|---|---|
| `slow` (default) | 3 e⁻ | 90 000 e⁻ | 1.0 ADU/e⁻ | 0.001 e⁻/s/pix |
| `fast` | 5 e⁻ | 90 000 e⁻ | 1.0 ADU/e⁻ | 0.001 e⁻/s/pix |

## PSF

The packaged `PSF_MAVIS_mcao.fits` holds the on-axis MCAO PSF at five
wavelengths (400–1000 nm) on a common 5.1″ window with 3.75 mas sampling:

- The **550 nm plane is the on-axis end-to-end MCAO PSF from MAVISIM**
  (Monty et al. 2021, MNRAS 507, 2192; LQG tomography simulations by
  J. Cranney, ANU). Measured performance: Strehl 0.35, ensquared energy
  0.40 in a 50 mas box. Because the kernel is identical to the one MAVISIM
  convolves with, ScopeSim V-band images match MAVISIM star-by-star to a
  few per cent (see `mavisim_comparison/`).
- The **other planes are an analytic model** (obscured VLT Airy core +
  AO-corrected halo + seeing halo) calibrated to the measured 550 nm
  Strehl via the Maréchal approximation. No end-to-end reference exists
  off V band — MAVISIM v1.1 is monochromatic — so treat non-V photometry
  as approximate.

The file is regenerated by `background_info/make_psf.py`, which needs the
MAVISIM repository (for `tests/test_psf_e2e.fits`).

### TipTop PSF alternative

`MAVIS_IMG.yaml` also carries a disabled `mavis_tiptop_psf` effect
(class `TipTopPSF`, requires a ScopeSim version that provides it plus
`pip install tiptop-ipy`). It generates the PSF on demand with ESO's
[TipTop](https://github.com/astro-tiptop/TIPTOP) simulator via the
University of Vienna TipTop server, one PSF per filter band at the band's
effective wavelength (max 1024×1024 pixels), cached on disk so each band
costs a single server call ever. Enable with:

```python
mavis["mavis_ao_psf"].include = False
mavis["mavis_tiptop_psf"].include = True
```

TipTop's default MAVIS configuration is more conservative than the MAVISIM
LQG simulations: Strehl 0.23 vs 0.35 at 550 nm, and 30–40 % less energy in
apertures below 150 mas.

### Field variation

None of the packaged PSFs vary across the field. For astrometric science
cases use the full field-varying MAVISIM PSF grid (11×11 positions, 1.7 GB:
<https://www.mso.anu.edu.au/~jcranney/mavisim_data/v1_1.tar.gz>) with
MAVISIM itself, or resample it into a ScopeSim `FieldVaryingPSF`.

(ifu-spectrograph)=
## IFU spectrograph

The IFU modes use ScopeSim's simple-IFU path (`LineSpreadFunction` +
`DetectorList3D` + `FluxBinning3D`), the same one METIS uses for its
`lms_cube` mode. **The output is a datacube** with axes (wavelength, y, x) —
there is no image slicer and no spectral trace list, so no dispersed detector
frame.

That is deliberate. The published material gives the IFU spaxel scales, fields
of view, resolving powers and wavelength ranges, but none of the spectrograph's
optical layout. A dispersed-image mode would have to invent the slice count,
the detector format and the dispersion geometry. The cube modes need none of
it, and everything they do need is either published or a stated sampling
convention.

### Selecting a mode

An IFU simulation needs **two** modes: one spatial scale and one spectral
configuration.

```python
import scopesim

cmd = scopesim.UserCommands(use_instrument="MAVIS",
                            set_modes=["IFU_FINE", "IFU_LR_BLUE"])
mavis = scopesim.OpticalTrain(cmd)
mavis.observe(src)
cube = mavis.readout()[0][1].data      # (2048, 144, 100)
```

```{warning}
Pick exactly one from each group. Selecting two spatial scales, or two
spectral configurations, loads the same yamls twice, which duplicates every
optical element and squares the system throughput.
```

### Spatial scales

| Mode | Spaxel | Field of view | Spaxels |
|---|---|---|---|
| `IFU_FINE` | 25 mas | 2.5″ × 3.6″ | 100 × 144 |
| `IFU_COARSE` | 50 mas | 5″ × 7.2″ | 100 × 144 |

The published spaxel sizes are ranges (20–25 mas fine, 40–50 mas coarse)
because the design was not frozen. The coarse end of each range is adopted.

### Spectral configurations

| Mode | R | Arm | Default `!OBS.wavelen` | Simultaneous window |
|---|---|---|---|---|
| `IFU_LR_BLUE` | 5 900 | 0.370–0.720 µm | 0.550 µm | 0.5184–0.5816 µm |
| `IFU_LR_RED` | 5 900 | 0.510–0.935 µm | 0.700 µm | 0.6598–0.7402 µm |
| `IFU_HR_BLUE` | 14 700 | 0.425–0.550 µm | 0.518 µm | 0.5060–0.5300 µm |
| `IFU_HR_RED` | 11 500 | 0.630–0.880 µm | 0.700 µm | 0.6793–0.7207 µm |

Each cube is 100 × 144 × 2048 voxels, about 118 MB as float32.

```{note}
**The window is not the arm.** Whether MAVIS observes a whole arm at once or
tunes across it is not stated publicly, and the numbers make a single-shot arm
implausible: R = 5900 over 370–720 nm is ~3900 resolution elements, which at
14 400 spaxels needs a MUSE-like multi-detector spectrograph. So the window is
a declared model parameter — 2048 bins wide — and `!OBS.wavelen` moves it
within the arm. Covering a whole arm at once would need ~11 800 bins and a
0.6 GiB cube.
```

### Retuning the observed wavelength

`!OBS.wavelen` can be moved, with two constraints.

```{warning}
The window must stay between two PSF wavelength-plane midpoints — at 0.475,
0.625, 0.775 and 0.925 µm for `PSF_MAVIS_mcao.fits`. A PSF effect splits the
`FieldOfView` at those wavelengths, and the cube modes cannot survive a split:
each sub-field is checked against the single `DetectorList3D` and the run
aborts on an assertion. The defaults above sit on a PSF plane, which is where
there is most room.
```

The spectral bin width is fixed per configuration, so the delivered resolving
power scales as `wavelen / default` if you retune — a few per cent over a
typical move. `background_info/tune_ifu_binning.py` recomputes a consistent
(wavelength, bin width) pair and checks both constraints.

### Verification

The test suite measures the delivered resolving power from an unresolved
emission line and checks it against the published R, verifies the cube
geometry and wavelength calibration, and closes the sky photon budget against
a hand integration of the skycalc emission spectrum. Results land in
[`radiometry_report.md`](radiometry_report.md).

(known-limitations)=
## Known limitations

- **PSF** is end-to-end (MAVISIM) at 550 nm only; the other wavelength
  planes are an analytic model calibrated to it. No plane has field
  variability, anisoplanatism or PSF elongation towards the field edge.
- **Filter curves** are the standard passbands MAVIS is expected to carry
  (ESO/FORS2 Bessell BVRI and the SDSS primed set), not measured MAVIS
  hardware — which does not exist yet.
- **AO module throughput** is a smooth approximation anchored on the 550 nm
  nominal value; a wavelength-resolved curve from the consortium is preferred.
- **QE curve** is approximate; manufacturer data preferred.
- **Dark current** (0.001 e⁻/s) and **MINDIT** (1 s) are estimates, not
  characterisations.
- **Narrow-band filters** are not included.
- **IFU modes output a datacube, not a dispersed frame.** The spectrograph's
  optical layout — slice count, detector format, dispersion geometry — is not
  published, so nothing about slice geometry, inter-slice gaps or
  detector-level artefacts is modelled. See
  [the planning documents](../background_info/planning/README.md).
- **IFU spectrograph throughput and grating efficiency are missing entirely**,
  so IFU fluxes are optimistic by whatever the spectrograph costs.
- **IFU detector properties are the imager CCD's**, themselves estimates. This
  matters more than it sounds: dark current is applied per voxel, correctly
  for a dispersed spectrograph, so it is multiplied by the 2048 spectral bins
  and dominates the sky in these windows.
- **The IFU simultaneous window is a model parameter, not a published one.**
  Each configuration covers a slice of its arm centred on `!OBS.wavelen`, not
  the whole arm; see below.
- The **sky** comes from `skycalc` with its default moon and airglow settings,
  which are brighter than dark time. Expect an implied V surface brightness
  near 20.5 mag/arcsec², not the canonical 21.6.

## Validation

A radiometry report with system-throughput plots is regenerated by the test
suite:

```bash
pytest MAVIS/tests/            # fast tests
pytest MAVIS/tests/ -m slow    # including radiometry and image tests
```

Output lands in [`radiometry_report.md`](radiometry_report.md).

A full imaging cross-validation against MAVISIM (PSF metrics, star-by-star
aperture photometry, sky levels) is produced by
`background_info/compare_mavisim.py`; results and figures live in
[`mavisim_comparison/`](mavisim_comparison/report.md). Headline result:
V-band aperture photometry agrees with MAVISIM to better than 6 % in
50–500 mas apertures.

## Reference material

Instrument specifications, source citations and the discrepancies between the
ESO baseline and the phase-A numbers are recorded in
[`../background_info/mavis_baseline_specification.md`](../background_info/mavis_baseline_specification.md).

### Instrument homepages

- [MAVIS at ESO](https://www.eso.org/sci/facilities/paranal/instruments/mavis.html)
- [MAVIS consortium](https://mavis-ao.org/mavis/)

### Key references

- Monty et al. 2021, MNRAS 507, 2192 — MAVISIM
- MAVIS science case — <https://arxiv.org/abs/2009.09242>
- Esposito et al. 2016, Proc. SPIE 9909, 99093U — optical MCAO sensitivity
