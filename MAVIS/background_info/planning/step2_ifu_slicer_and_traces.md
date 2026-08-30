# Step 2: Dispersed-image IFU modes — slicer and spectral traces

## Goal

Model the IFU the way the instrument actually works: slice the field, disperse
each slice, and lay the spectra onto real detectors, so that simulations
produce raw-frame-like output rather than a datacube.

## Status: blocked

This step cannot be started responsibly on public information. Everything it
needs is unpublished, and guessing it would put invented instrument geometry
into a reference database.

## What ScopeSim needs

The reference implementation is METIS LMS
(`METIS/METIS_LMS.yaml` + `METIS/TRACE_LMS.fits`), with
`MOSAIC/MOSAIC_VIS.yaml` as a second example.

### 1. An image slicer

`MetisLMSImageSlicer` (subclass of `ApertureMask`), reading an
`Aperture List` extension from the trace file. Needs:

- **number of slices** across the IFU field
- **slice width** on sky [arcsec]
- **slice length** on sky [arcsec]
- slice ordering on the detector (which slice lands where)

### 2. A spectral trace list

`SpectralTraceList` or a MAVIS subclass, reading a trace FITS whose structure
is (verified against `METIS/TRACE_LSS_M.fits`):

```
PRIMARY   ECAT, EDATA, AUTHOR, SOURCE, DESCRIPT, DATE-CRE, DATE-MOD, STATUS
TOC       BinTable: description, extension_id, aperture_id, image_plane_id
<trace>   BinTable per trace: wavelength [um], xi [arcsec], x [mm], y [mm]
```

`xi` is position along the slice; `x`, `y` are focal-plane coordinates in mm.
So one trace table per slice per configuration. Needs:

- **dispersion direction and law** — linear, or the actual grating equation
  with its non-linearity
- **plate scale at the spectrograph focal plane** [arcsec/mm]
- **slice-to-detector mapping** — where each slice's spectrum lands,
  including any tilt or curvature
- **order layout**, if the gratings are used in more than one order

### 3. A detector layout

`DetectorList` with the real focal-plane geometry: format, pixel pitch,
number of detectors, and their positions and gaps.

## The scale problem

Worth stating explicitly, because it constrains any future design:

- Fine scale at 25 mas over 2.5″ × 3.6″ is 100 × 144 = **14 400 spaxels**.
- LR-Blue at R = 5 900 over 370–720 nm is ~3 900 resolution elements,
  ~7 900 pixels along dispersion at Nyquist.
- Spaxels × spectral pixels is ~1.1 × 10⁸ detector samples.

A 4k × 4k detector holds 1.7 × 10⁷ pixels, so MAVIS needs of order **8 such
detectors**, or a smaller simultaneous wavelength window, or both. MUSE
solves the same problem with 24 separate IFU units, each with its own
spectrograph and detector.

Which of these MAVIS does is exactly the unpublished information that blocks
this step, and it is also
[open question 1.2 in step 1](step1_ifu_cube_mode.md).

## What to ask the consortium for

In rough priority order:

1. Whether the quoted wavelength ranges are simultaneous or tunable, and if
   tunable, the simultaneous window.
2. The number of IFU units / spectrograph channels and their detectors:
   format, pixel pitch, mosaic geometry.
3. Slicer geometry: slice count, width, length, and the slice-to-detector
   mapping.
4. The dispersion solution per configuration — ideally as a trace file or a
   polynomial mapping (λ, xi) → (x, y), which is directly convertible to the
   FITS format above.
5. Whether the fine and coarse scales share a spectrograph or have separate
   optical paths.

Items 1–3 are enough to start; 4 is what makes the model quantitative.

## Verification, once unblocked

- Each slice's spectrum lands where the trace says, to sub-pixel accuracy.
- The wavelength solution recovered from a simulated arc frame matches the
  input dispersion.
- Resolving power measured from simulated arc lines matches the published R
  per configuration.
- Total flux through the dispersed path matches the cube mode from step 1 to
  within the slicer losses.
- Inter-slice gaps and detector gaps appear in the right places.

## ScopeSim effects used

| Effect | Purpose |
|---|---|
| `MetisLMSImageSlicer` or an `ApertureList` | Field slicing |
| `SpectralTraceList` / `SpectralTraceListWheel` | Spectra onto the detector |
| `MetisLMSEfficiency` or `TERCurve` | Grating efficiency (step 3) |
| `DetectorList` | Spectrograph focal-plane geometry |

A MAVIS-specific `SpectralTraceList` subclass is probably **not** needed —
`MetisLMSSpectralTraceList` exists because METIS LMS has a tunable central
wavelength across grating orders. If MAVIS turns out to be tunable in the
same way, that class is the model to follow; otherwise the generic
`SpectralTraceList` should be enough.
