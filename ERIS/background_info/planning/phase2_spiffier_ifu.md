# Phase 2: SPIFFIER IFU Spectrograph

## Goal
Implement the SPIFFIER integral field spectrograph arm of ERIS, enabling
J, H, and K band spectroscopy at R~5000 (low-res) and R~10000 (high-res)
over three spatial scales (25mas, 100mas, 250mas).

## Instrument Specifications

### Optical Path
1. Light enters from ERIS warm optics (same as NIX, via selector mirror)
2. **Pre-optics:**
   - Triplet collimator lens
   - Cold stop (6mm diameter, with central obscuration matching UT4 secondary)
   - Motorised filter wheel (band-pass filters to suppress grating diffraction orders)
   - Motorised optics wheel (3 interchangeable zoom lens sets for 25/100/250mas)
3. **Image slicer:**
   - 32 plane mirrors (small slicer) → slice image into 32 slitlets
   - 32 mirrors (big slicer) → rearrange slitlets into 31cm pseudo-slit
   - Material: zero-expansion glass, optically contacted
   - Slitlets run horizontally on detector, numbered top-to-bottom
4. **Spectrometer collimator:**
   - 3 diamond-turned gold-coated aluminium mirrors (M1 spherical, M2/M3 oblate elliptical)
5. **Grating wheel:**
   - 4 gratings total (3 low-res blazed per-band + 1 high-res for all bands)
   - Grating wheel precision: 1:647 gear ratio, 1/5 pixel accuracy
6. **Camera:**
   - 5 lenses (170mm diameter for 3 largest) + 1 folding mirror
   - f/2.8 design
   - Multi-layer AR coating optimized for 1.05-2.45μm

### Spatial Scales

| Scale | Spaxel Size | FoV | Pixels |
|-------|------------|-----|--------|
| 25mas | 12.5 × 25 mas | 0.8" × 0.8" | 64 × 32 |
| 100mas | 50 × 100 mas | 3.2" × 3.2" | 64 × 32 |
| 250mas | 125 × 250 mas | 8.0" × 8.0" | 64 × 32 |

Note: Spaxels are rectangular (2:1 aspect ratio). The 32 slices correspond to
the "long" axis of the spaxel; the 64 pixels per slice correspond to the "short" axis.

### Grating Configurations (12 total)

**Low resolution (R~5000):**

| Config | λ_c [μm] | Range [μm] | R |
|--------|----------|-----------|---|
| J_low | 1.25 | 1.09-1.42 | 5000 |
| H_low | 1.66 | 1.45-1.87 | 5200 |
| K_low | 2.21 | 1.93-2.48 | 5600 |

**High resolution (R~10000):**

| Config | λ_c [μm] | Range [μm] | R |
|--------|----------|-----------|---|
| J_short | 1.18 | 1.10-1.27 | 10000 |
| J_middle | 1.26 | 1.18-1.35 | 10000 |
| J_long | 1.34 | 1.26-1.43 | 10000 |
| H_short | 1.56 | 1.46-1.67 | 10400 |
| H_middle | 1.67 | 1.56-1.77 | 10400 |
| H_long | 1.76 | 1.66-1.87 | 10400 |
| K_short | 2.07 | 1.93-2.22 | 11200 |
| K_middle | 2.20 | 2.06-2.34 | 11200 |
| K_long | 2.33 | 2.19-2.47 | 11200 |

### Detector
- Teledyne HAWAII 2RG (2048×2048), separate from NIX detector
- Wavelength cutoff: 2.5μm (different from NIX's 5μm cutoff)
- Operating temperature: 77K (liquid nitrogen bath)
- Pixel size: 18μm
- Dark current: 0.19 e-/s
- Well depth: >80k e-
- Gain: 2.0 e-/ADU
- Readout noise: 12e- (2s), 7e- (60s), 11e- (600s)
- Min DIT: 1.6s (full frame)
- Non-linearity: ~3% at 20k ADU
- Readout: Up-the-ramp (UTR) only (no fast mode)
- Bad pixels: ~10-pixel diameter cold pixel cluster in slitlet 16

---

## Implementation Architecture

### YAML Files

```
ERIS_SPIFFIER.yaml              # Common IFU optics (pre-optics, collimator, camera)
ERIS_SPIFFIER_25.yaml           # 25mas scale config + SIM spectral override
ERIS_SPIFFIER_100.yaml          # 100mas scale config
ERIS_SPIFFIER_250.yaml          # 250mas scale config
ERIS_SPIFFIER_H2RG.yaml         # SPIFFIER detector (separate from NIX)
```

### Mode Definitions in default.yaml

Each SPIFFIER mode combines a spatial scale + grating configuration.
Since there are 3 scales × 12 gratings = 36 combinations, the grating
selection should be a property (not a separate mode):

```yaml
# In default.yaml mode_yamls:
- object: observation
  alias: OBS
  name: ifsJ_25
  description: "SPIFFIER J-band low-res at 25mas"
  yamls:
    - ERIS_SPIFFIER.yaml
    - ERIS_SPIFFIER_25.yaml
    - ERIS_SPIFFIER_H2RG.yaml
  properties:
    grating: J_low
    trace_file: TRACE_SPIFFIER_J_low.fits
    efficiency_file: TER_grating_J_low.dat
    filter_name: J_ifs
    spectral_resolution: 5000
```

Alternatively, use fewer modes with the grating as a switchable property:
```yaml
- object: observation
  alias: OBS
  name: ifs_25
  description: "SPIFFIER IFU at 25mas pixel scale"
  yamls: [ERIS_SPIFFIER.yaml, ERIS_SPIFFIER_25.yaml, ERIS_SPIFFIER_H2RG.yaml]
  properties:
    grating: J_low       # user changes this
    trace_file: "TRACE_SPIFFIER_J_low.fits"
    efficiency_file: "TER_grating_J_low.dat"
```

This gives 3 modes (ifs_25, ifs_100, ifs_250) with grating selection via properties.

### Data Files Required

**Surface lists:**
- `LIST_ERIS_spiffier_preoptics.dat` — Collimator triplet + cold stop + filter
- `LIST_ERIS_spiffier_zoom_25.dat` — 25mas zoom optics (2-3 lenses)
- `LIST_ERIS_spiffier_zoom_100.dat` — 100mas zoom optics
- `LIST_ERIS_spiffier_zoom_250.dat` — 250mas zoom optics
- `LIST_ERIS_spiffier_collimator.dat` — 3 gold mirrors (spherical + 2 elliptical)
- `LIST_ERIS_spiffier_camera.dat` — 5 lenses + 1 fold mirror

**Detector files:**
- `FPA_spiffier_layout.dat` — Single H2RG chip (same format as NIX)
- `FPA_spiffier_linearity.dat` — Non-linearity curve (~3% at 20k ADU)
- `QE_H2RG_2p5um.dat` — QE for 2.5μm cutoff detector (reuse HAWKI_new data)

**Spectral trace files (FITS):** One per grating configuration (12 total initially,
start with 3 low-res):
- `TRACE_SPIFFIER_J_low.fits`
- `TRACE_SPIFFIER_H_low.fits`
- `TRACE_SPIFFIER_K_low.fits`
- (9 high-res traces: J/H/K × short/middle/long)

**Grating efficiency files:**
- `TER_grating_J_low.dat` (or .fits)
- `TER_grating_H_low.dat`
- `TER_grating_K_low.dat`
- (9 high-res efficiency files)

**IFU filter files:**
- `TC_filter_J_ifs.dat` — J-band order-sorting filter for SPIFFIER
- `TC_filter_H_ifs.dat` — H-band
- `TC_filter_K_ifs.dat` — K-band

---

## ScopeSim Effects — What Exists vs What's Missing

### Approach A: Generic SpectralTraceList (Recommended Starting Point)

Use the same approach as MICADO SPEC, with one trace per IFU slice:

| Effect | Status | Usage |
|--------|--------|-------|
| `ApertureMask` | **Exists** | Define overall IFU FoV |
| `SpectralTraceList` | **Exists** | Map 32 slice traces to detector |
| `SpectralEfficiency` | **Exists** | Grating blaze function |
| `SurfaceList` | **Exists** | Collimator, camera, zoom optics |
| `FilterWheel` / `FilterCurve` | **Exists** | Order-sorting filters |
| `DetectorList` | **Exists** | Single H2RG |
| `DetectorModePropertiesSetter` | **Exists** | Readout parameters |

The `SpectralTraceList` FITS file would contain:
- HDU 0: PrimaryHDU with ECAT=1, EDATA=2
- HDU 1: BinTableHDU catalog — 32 rows (one per slice)
- HDU 2-33: BinTableHDU trace tables — one per slice, each with columns:
  - `wavelength` [um]: wavelength grid across the grating band
  - `xi` [arcsec]: spatial position along the slice
  - `x` [mm]: detector x position
  - `y` [mm]: detector y position

### Approach B: METIS LMS-style (More Physically Accurate)

Use polynomial-based trace mapping like METIS LMS:

| Effect | Status | Usage |
|--------|--------|-------|
| `MetisLMSImageSlicer` | **Exists but METIS-specific** | IFU slice geometry |
| `MetisLMSSpectralTraceList` | **Exists but METIS-specific** | Polynomial trace mapping |
| `MetisLMSEfficiency` | **Exists but METIS-specific** | Echelle blaze computation |

Would need to either:
1. Generalize the METIS LMS effects into generic `ImageSlicer`, `IFUSpectralTraceList`
2. Or create ERIS-specific versions

### Recommended Path
**Start with Approach A** (generic SpectralTraceList). This is simpler and
sufficient for the skeleton. The main challenge is generating the trace FITS files.

### Missing: Image Slicer Aperture Definition

The 32 IFU slices need to be defined as apertures. Options:

**Option 1:** Single `ApertureMask` for the overall FoV
- Simple but doesn't model individual slices
- Each trace in the SpectralTraceList maps to a different spatial region
- The SpectralTraceList handles the mapping internally

**Option 2:** `ApertureList` (from a FITS table)
- Define 32 rectangular apertures in the SpectralTraceList FITS file
- Each aperture has: id, left, right, top, bottom, angle, conserve_image
- Requires the SpectralTraceList to handle multiple apertures → it already does

**Option 3:** Write a new `ImageSlicer` effect
- A generic version of MetisLMSImageSlicer
- Reads slice geometry from a table
- Creates aperture masks for each slice
- Most physically correct but most work

**Recommended:** Option 1 for the skeleton, with upgrade to Option 2 later.

---

## Generating Spectral Trace Files

This is the most challenging part of Phase 2. The trace files encode the
mapping from (wavelength, slice_position) → (detector_x, detector_y) for
each of the 32 slices.

### What We Know
- 32 slices, each 64 pixels wide on the detector
- Slitlets run horizontally, light dispersed vertically
- Brick-wall pattern on detector (slitlets interleaved)
- Grating dispersion: known spectral resolution and wavelength range
- Total detector: 2048 × 2048 pixels, 18μm pixel size

### Approach to Generate Traces

1. **Layout model:** Each slice occupies ~64 columns on the detector.
   32 slices × 64 columns = 2048 columns (fills detector width).
   The "brick-wall" pattern means alternating slices are offset vertically.

2. **Dispersion model:** For each grating configuration:
   - Linear dispersion: dλ/dy = (λ_max - λ_min) / N_rows
   - E.g., K_low: (2.48 - 1.93) / 2048 = 0.000268 μm/pixel

3. **Spatial model:** For each slice:
   - x position on detector = slice_center + xi × plate_scale_ratio
   - y position = f(wavelength) via dispersion relation

4. **Script:** Write a Python script that:
   - Takes grating parameters (λ_min, λ_max, R)
   - Takes slice geometry (32 slices, positions on detector)
   - Computes trace tables for each slice
   - Packages into FITS with SpectralTraceList format

### Reference Data Sources
- The SINFONI package in irdb (`D:\Repos\irdb\SINFONI\`) has a user manual PDF
  but no trace data
- The METIS TRACE_LMS.fits provides a format reference
- ESO SPIFFIER pipeline documentation may have distortion models
- Commissioning data may provide empirical trace positions

### Estimated Effort
- Generating approximate traces (linear dispersion, uniform slice spacing): 1-2 days
- Validating against real SPIFFIER data: requires access to calibration frames
- Full 12-grating set: multiply by 4 (3 low-res easy, 9 high-res are subsets)

---

## Phase 2 Build Order

### Phase 2a: K_low at 100mas (Simplest Starting Point)
1. Create `ERIS_SPIFFIER.yaml` with pre-optics surface list
2. Create `ERIS_SPIFFIER_100.yaml` with 100mas scale config
3. Create `ERIS_SPIFFIER_H2RG.yaml` with detector chain
4. Generate `TRACE_SPIFFIER_K_low.fits` with approximate linear traces
5. Create `TER_grating_K_low.dat` with estimated blaze function
6. Add `ifs_100` mode to default.yaml
7. Test: observe point source, verify 32 spectra appear on detector

### Phase 2b: All Low-Res Gratings + All Scales
1. Generate J_low and H_low trace files
2. Add 25mas and 250mas scale YAMLs
3. Create order-sorting filter curves (J_ifs, H_ifs, K_ifs)
4. Add all low-res modes to default.yaml

### Phase 2c: High-Res Gratings
1. Generate 9 high-res trace files (J/H/K × short/middle/long)
2. Each high-res grating covers half the band at double resolution
3. Add high-res modes to default.yaml

### Phase 2d: Validation
1. Compare spectral resolution against SPIFFIER specs
2. Verify wavelength calibration
3. Compare throughput/sensitivity
4. Test cube reconstruction
