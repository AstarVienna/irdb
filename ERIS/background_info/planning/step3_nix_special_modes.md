# Step 3: NIX Special Modes (APP, FPC, SAM, LSS)

## Goal
Add skeleton mode YAMLs for the four non-standard NIX observing modes.
The priority order is LSS (most straightforward), then APP/FPC/SAM (all require
custom PSF handling).

---

## 3.1 — nixLSS (Long Slit Spectroscopy, L-band)

### Instrument Specifications
- Slit: 86 mas wide × 12" long
- Grism: Position 12 in pupil wheel, L-band
- Camera: LM-13mas (13.03 mas/pix)
- Filter: L-Broad (3.0-4.2μm, FWHM 1.04μm)
- Spectral resolution: R ~ 900 (measured R=970)
- Wavelength coverage: 3.05-4.05 μm
- Dispersion direction: vertical (close to vertical on detector)
- Slit orientation: horizontal (along detector rows)

### Files to Create

**`MASK_slit_nix_lss.dat`** — Slit aperture definition (ASCII)
```
# description : ERIS NIX LSS slit 86mas x 12arcsec
# type : aperture:slit_geometry
# x_unit : arcsec
# y_unit : arcsec
x        y
-6.0     -0.043
 6.0     -0.043
 6.0      0.043
-6.0      0.043
```
Note: The slit is 12" long (±6") and 86mas wide (±43mas). The long axis is
along x (spatial direction), dispersion is along y.

**`TRACE_NIX_LSS_L.fits`** — Spectral trace geometry (FITS)
Must follow ScopeSim SpectralTraceList format:
- HDU 0: PrimaryHDU with `ECAT=1`, `EDATA=2`
- HDU 1: BinTableHDU "TOC" — catalog with columns: description, extension_id, aperture_id, image_plane_id
- HDU 2: BinTableHDU "LSS_L" — trace table with columns:
  - `wavelength` [um]: wavelength grid (3.0-4.2μm, ~100 points)
  - `xi` [arcsec]: spatial position along slit (sample at e.g. -6, -3, 0, 3, 6)
  - `x` [mm]: focal plane x position
  - `y` [mm]: focal plane y position

The trace must encode the grism dispersion relation. At R~900 and λ_c=3.57μm,
the dispersion is approximately:
- dλ/dpix ≈ λ/(R × N_pix) ≈ 3.57/(900×2048) × 1000 ≈ 0.004 μm/pixel ??? (need to verify)
- More accurately: 1.0μm bandwidth across ~2048 pixels → ~0.0005 μm/pixel
- This gives ~770 pixels per R element at 3.57μm → R ~ 900 checks out

The trace maps (wavelength, xi) → (x, y) on the focal plane where:
- x depends mainly on xi (spatial position → horizontal on detector)
- y depends mainly on wavelength (dispersion → vertical on detector)

**`TER_grism_L.fits`** — Grism efficiency (FITS)
Same format as SpectralEfficiency:
- HDU 0: PrimaryHDU with `ECAT=1`, `EDATA=2`
- HDU 1: BinTableHDU catalog
- HDU 2: BinTableHDU with columns: wavelength [um], efficiency [0..1]
  - Blaze function peaking near 3.5μm, ~80% peak efficiency, falling to ~50% at edges

**`ERIS_NIX_LSS.yaml`** — Mode configuration
```yaml
object: instrument
alias: INST
name: ERIS_NIX_LSS
description: NIX L-band long-slit spectroscopy R~900

properties:
  pixel_scale: 0.01303
  plate_scale: 0.7239
  decouple_detector_from_sky_headers: True

effects:
  - name: nix_lss_field_of_view
    class: ApertureMask
    kwargs:
      array_dict:
        x: [-13.2, 13.2, 13.2, -13.2]
        y: [-13.2, -13.2, 13.2, 13.2]
      x_unit: arcsec
      y_unit: arcsec

  - name: nix_lm13_camera_optics
    class: SurfaceList
    kwargs:
      filename: LIST_ERIS_nix_optics_lm13.dat

  - name: nix_lss_slit
    class: ApertureMask
    kwargs:
      filename: MASK_slit_nix_lss.dat

  - name: nix_lss_spectral_traces
    class: SpectralTraceList
    kwargs:
      filename: TRACE_NIX_LSS_L.fits
      wave_colname: wavelength
      s_colname: xi
      col_number_start: 1

  - name: nix_lss_grism_efficiency
    class: SpectralEfficiency
    kwargs:
      filename: TER_grism_L.fits
```

### ScopeSim Effects Required
All already exist:
- `ApertureMask` — slit definition
- `SpectralTraceList` — trace geometry
- `SpectralEfficiency` — grism blaze function
- `SurfaceList` — camera optics

### Generating the Trace File
A Python script is needed to compute the FITS trace file from the grism
dispersion relation. The approach:
1. Define a wavelength grid (3.0-4.2μm, 120 steps)
2. Define spatial positions along the slit (-6" to +6", 25 steps)
3. For each (wavelength, xi), compute (x, y) on the focal plane:
   - x = xi / plate_scale (spatial position maps linearly to x)
   - y = (wavelength - λ_ref) × dispersion_mm_per_um + y_ref
4. Write to FITS using the SpectralTraceList format

Reference: METIS TRACE_LSS_L.fits and MICADO TRACE_MICADO.fits for format examples.

---

## 3.2 — nixAPP (Apodizing Phase Plate Coronagraphy)

### Instrument Specifications
- Pupil wheel element: APP (position 6)
- Camera: 13mas-LM (for L and M bands; also usable with JHK-13mas)
- Tracking: Pupil tracking mode (mandatory for ADI)
- PUP_ANGLE: 36° for all APP observations
- PSF structure: THREE images per source:
  - Central image: ~2% of stellar flux (photometric reference)
  - Two outer PSFs: ~49% each, with D-shaped dark regions on opposite sides
- Designed for narrowband filters (Br-g, K-peak, H2-1-0S, Br-a, Br-a-cont)
- Broadband filters cause radial PSF smearing (chromatic leakage)

### Optical Model
The APP is a pupil-plane phase optic that modifies the PSF. It does NOT change
the throughput significantly — it redistributes the PSF flux.

**What ScopeSim needs to model this:**
1. A pre-computed PSF FITS file that includes the APP diffraction pattern convolved
   with the AO PSF (wavelength-dependent)
2. The PSF file must be in `FieldConstantPSF` format (FITS with wavelength-dependent
   2D PSF layers)
3. The PSF should show the characteristic 3-spot pattern with D-shaped dark holes

**There is NO existing ScopeSim effect for APP.** The workaround is:
- Generate APP PSFs externally (using Fourier optics code, e.g. HCIPy or poppy)
- Store as FITS cubes compatible with `FieldConstantPSF`
- The AO mode YAML provides the atmospheric PSF, but for APP the PSF must be
  replaced entirely with the combined AO+APP PSF

### Potential New ScopeSim Effect: `ApodizingPhasePlate`
If we wanted a proper optical model rather than pre-computed PSFs:
- **Input:** Phase pattern of the APP optic (2D array in pupil plane)
- **Operation:** Multiply the pupil-plane electric field by the APP phase pattern,
  then Fourier transform to get the focal-plane PSF
- **Output:** Wavelength-dependent PSF with the 3-spot pattern
- **Complexity:** Medium — requires Fourier optics (poppy or similar)
- **Alternative:** Stay with pre-computed PSFs (recommended for skeleton)

### Files to Create
- `ERIS_NIX_APP.yaml` — Mode YAML referencing APP PSF and camera optics
- `psfs/PSF_APP_Ks.fits` (etc.) — Pre-computed APP PSF files per filter/wavelength

### Mode YAML Structure
```yaml
effects:
  - name: nix_field_of_view  # 26.4" FoV (13mas camera)
    class: ApertureMask
  - name: nix_camera_optics
    class: SurfaceList
    kwargs: {filename: LIST_ERIS_nix_optics_jhk13.dat}
  # APP PSF replaces AO PSF — must be handled at the AO mode level
  # or by disabling eris_ao_psf and adding a separate APP PSF effect
```

---

## 3.3 — nixFPC (Focal Plane Coronagraphy / Vortex Coronagraph)

### Instrument Specifications
- Coronagraph type: AGPM (Annular Groove Phase Mask) vortex coronagraph
- Two masks: AGPM-L (L-band) and AGPM-M (M-band)
- Lyot stop: Spider mask + undersized circular aperture (position 10 in pupil wheel)
- Lyot-ND: Lyot + neutral density (~4.5 mag attenuation, position 11)
- Camera: 13mas-LM
- Tracking: Pupil tracking mode (mandatory)
- PUP_ANGLE: 135° for all FPC observations
- Inner working angle: ~1 λ/D (coronagraphic transmission >50% at 1 λ/D)
- Throughput: 83% L-band substrate, 68% M-band substrate
  Combined with Lyot stop: 62% L-band, 51% M-band
- Max FoV radius: 8.2"
- Active centring: QACITS algorithm (pointing accuracy 0.014-0.02 λ/D)
- Bright limit: L < 3.7 (or L > -2 with Lyot-ND + window3)
- Faint limit: L < 8

### Optical Model
The vortex coronagraph consists of:
1. **AGPM** in the focal plane — imprints an optical vortex phase on the on-axis starlight
2. **Lyot stop** in the subsequent pupil plane — blocks the diffracted starlight

The combined effect rejects on-axis point-source light while transmitting off-axis
sources (companions, disks) with position-dependent throughput.

**What ScopeSim needs to model this:**
1. A coronagraphic PSF that shows the residual on-axis starlight (after AGPM+Lyot rejection)
2. A throughput map showing the off-axis transmission as a function of angular separation
   (the coronagraphic transmission curve: ~0% at 0", >50% at 1 λ/D, ~100% at >3 λ/D)
3. The Lyot stop throughput reduction (~15-38% depending on band)

**There is NO existing ScopeSim effect for vortex coronagraphs.**

### Potential New ScopeSim Effect: `VortexCoronagraph`
- **Input:** Vortex charge (typically 2 for AGPM), Lyot stop geometry, wavelength
- **Operation:**
  1. Apply vortex phase in focal plane
  2. Propagate to pupil plane (inverse Fourier transform)
  3. Apply Lyot stop mask
  4. Propagate back to focal plane (Fourier transform)
- **Output:** Coronagraphic PSF + off-axis transmission map
- **Complexity:** High — requires full Fourier optics propagation
- **Alternative:** Pre-computed coronagraphic PSFs (recommended)
  - On-axis PSF: residual starlight after AGPM rejection
  - Off-axis throughput: simple radial transmission curve (1D)
  - Could be implemented as a `FieldConstantPSF` for the on-axis case
    plus a `TERCurve`-like radial mask for off-axis attenuation

### Simpler Workaround Model
For the skeleton package, model FPC as:
1. `FieldConstantPSF` with a pre-computed coronagraphic PSF (residual starlight)
2. `TERCurve` representing the Lyot stop throughput loss (flat ~62% L, ~51% M)
3. Ignore the position-dependent coronagraphic transmission for now
   (treat companions as if they have full throughput beyond 1 λ/D)

### Files to Create
- `ERIS_NIX_FPC.yaml` — Mode YAML
- `TER_lyot_stop_L.dat` — Lyot stop throughput (flat ~62%)
- `TER_lyot_stop_M.dat` — Lyot stop throughput (flat ~51%)
- `psfs/PSF_FPC_AGPM_L.fits` — Pre-computed coronagraphic PSF for L-band
- `psfs/PSF_FPC_AGPM_M.fits` — Pre-computed coronagraphic PSF for M-band

---

## 3.4 — nixSAM (Sparse Aperture Masking)

### Instrument Specifications

**SAM-7 mask:**
- 7 apertures, 21 non-redundant baselines
- Throughput: 14%
- Best for faint targets (highest throughput of the three)

**SAM-9 mask:**
- 9 apertures, 36 non-redundant baselines
- Throughput: 10.6%
- Intermediate brightness targets

**SAM-23 mask:**
- 23 apertures, 253 baselines (173 non-redundant)
- Throughput: 5%
- Partially redundant; best for bright targets
- Resolution factor of 2 better than telescope diffraction limit

**Common specs:**
- Camera: 13mas-JHK or 13mas-LM
- Tracking: Pupil tracking mode (mandatory)
- PUP_ANGLE: 34° (SAM-23 with JHK-13mas), 136° (all others)
- Inner working angle: 0.5 λ/D for all masks
- Filters: Any (broad or narrow band)
- Data processing: Not pipeline-processed; uses AMICAL software
- Calibration: Interleaved calibrator star observations required

### Optical Model
Each SAM mask places N holes in the pupil plane. The resulting focal-plane
image is an interferogram — the coherent combination of light from all
aperture pairs. The PSF is the Fourier transform of the aperture pattern
(not a simple Airy pattern).

**What ScopeSim needs to model this:**
1. A PSF for each mask configuration that shows the interferometric fringe pattern
2. The overall throughput reduction (5-14% depending on mask)

**There is NO existing ScopeSim effect for SAM.**

### Potential New ScopeSim Effect: `SparseApertureMask`
- **Input:** Aperture positions and radii (from User Manual Table 14/15/16),
  telescope pupil geometry
- **Operation:**
  1. Create binary pupil mask with N circular apertures
  2. Fourier transform to get interferometric PSF
  3. Scale by throughput (ratio of mask area to full pupil area)
- **Output:** Wavelength-dependent interferometric PSF
- **Complexity:** Medium — straightforward Fourier optics
  (simpler than coronagraphy because no phase elements)
- **Data available:** Aperture hole positions and radii are tabulated in the
  User Manual (Table 14 for SAM-7, Table 15 for SAM-9, Table 16 for SAM-23),
  for both 13mas-JHK and 13mas-LM cameras

### Workaround Model
For the skeleton package:
1. Pre-compute SAM PSFs using poppy or similar (Fourier transform of mask geometry)
2. Store as `FieldConstantPSF` FITS files
3. Apply throughput reduction via a `TERCurve` (flat 14%, 10.6%, or 5%)

### Files to Create
- `ERIS_NIX_SAM.yaml` — Mode YAML with configurable mask selection
- `TER_sam7_throughput.dat` — Flat 14% transmission
- `TER_sam9_throughput.dat` — Flat 10.6% transmission
- `TER_sam23_throughput.dat` — Flat 5% transmission
- `psfs/PSF_SAM7.fits` — Pre-computed SAM-7 interferometric PSF
- `psfs/PSF_SAM9.fits` — Pre-computed SAM-9 interferometric PSF
- `psfs/PSF_SAM23.fits` — Pre-computed SAM-23 interferometric PSF

---

## Summary of New ScopeSim Effects Needed

| Effect | Mode | Complexity | Recommended Approach |
|--------|------|-----------|---------------------|
| `ApodizingPhasePlate` | nixAPP | Medium | Pre-computed PSF files (poppy/HCIPy) |
| `VortexCoronagraph` | nixFPC | High | Pre-computed coronagraphic PSF files |
| `SparseApertureMask` | nixSAM | Medium | Pre-computed interferometric PSF files (poppy) |
| `SpectralTraceList` (data) | nixLSS | Low | Generate FITS trace file from grism specs |

For all three high-contrast modes (APP, FPC, SAM), the recommended skeleton approach
is pre-computed PSF FITS files loaded via `FieldConstantPSF`. Full Fourier optics
effects could be developed later in ScopeSim if there is demand for on-the-fly
PSF computation.

The LSS mode requires no new ScopeSim effects — only data files (trace FITS,
efficiency FITS, slit mask).
