# Step 2: Complete Optics Data, All Filters, LM Band Support

## Goal
Replace placeholder optics data with proper material-specific transmission curves,
and ensure LM-band (3-5μm) thermal background is correctly handled.

## Current State
- JHK-13mas mode works with all 17 filters from SVO
- Camera optics surface list uses CaF2 window transmission as placeholder for all lens elements
- JHK-27mas and LM-13mas modes exist but share the JHK-13mas optics file
- ChopNodCombiner not yet enabled for LM modes

## Tasks

### 2.1 — Proper camera optics surface lists

The NIX camera barrel has 3 camera configurations, each with 3 lenses made from
different materials (BaF2, IRG2/Schott chalcogenide, ZnSe) plus fold mirrors.

**Files to create:**
- `TER_lens_BaF2.dat` — Barium Fluoride transmission (0.15-12μm window, ~93% per surface)
- `TER_lens_IRG2.dat` — Schott IRG2 chalcogenide glass (~85-90% in NIR, drops in MIR)
- `TER_lens_ZnSe.dat` — Zinc Selenide transmission (0.5-22μm, ~70% per element at NIR due to high refractive index)

**Source data:** Standard optical material databases (Schott, II-VI, literature).
Each file should cover 0.8-6.0μm with proper absorption features.

**Update surface lists:**
- `LIST_ERIS_nix_optics_jhk13.dat` — 3 lenses (BaF2, IRG2, ZnSe) + 2 fold mirrors (gold)
- `LIST_ERIS_nix_optics_jhk27.dat` — 3 lenses + 1 fold mirror (different camera barrel, 1 fewer fold)
- `LIST_ERIS_nix_optics_lm13.dat` — 3 lenses optimized for 3-5μm + 2 fold mirrors

**Throughput targets (Davies+2023):**
- Instrument-only (without telescope/atmosphere): 70-75% for JHK, 65-70% for LM
- Total (with telescope+atmosphere+QE): 42% J, 61% H, 52% K

### 2.2 — Pupil wheel elements as TERCurves

The NIX pupil wheel contains cold stops that affect throughput differently for JHK vs LM:
- **JHK-pupil** (position 1): Metal plate with circular aperture — reduces thermal background slightly
- **LM-pupil** (position 3): Smaller circular aperture — more aggressive thermal blocking
- **Spider mask** (position 4): Blocks secondary mirror and spider emission, ~15% throughput reduction

These should be modelled as `TERCurve` effects with flat transmission values,
or as `PupilTransmission` if that is more appropriate. The pupil element is
currently not modelled — it only affects the effective collecting area and
background level.

**Approach:** Add a pupil wheel `FilterWheel` or a simple `TERCurve` per-mode that
represents the selected pupil stop's throughput and emissivity. For the skeleton
package, flat transmission values are sufficient:
- JHK-pupil: 0.98 transmission (barely undersized)
- LM-pupil: 0.95 transmission (more undersized)
- Spider mask: 0.85 transmission (blocks 15% of pupil)

### 2.3 — ChopNodCombiner for LM band

Thermal background at 3-5μm requires chopping and nodding for background subtraction.

**Changes:**
- `ERIS_NIX_H2RG.yaml` already has a placeholder for ChopNodCombiner (currently missing)
- Add it with `include: false` by default
- `ERIS_NIX_IMG_LM13.yaml` mode properties should set:
  ```yaml
  properties:
    chop_offsets: [5, 0]
    nod_offsets: [0, 5]
  ```
- The ChopNodCombiner effect should be enabled via mode properties

**ScopeSim effect:** `ChopNodCombiner` (already exists)
- Parameters: `chop_offsets`, `nod_offsets`, `pixel_scale`
- Combines: AA - AB - (BA - BB)

### 2.4 — Verification

- Compare system throughput in J, H, K against published values (42%, 61%, 52%)
- Verify LM-band thermal background level is physically sensible
- All 17 filters should produce images with reasonable S/N for standard star sources
- ChopNod should reduce LM-band background

## ScopeSim Effects Used
All effects already exist in ScopeSim — no new effects needed for this step.

| Effect | Purpose |
|--------|---------|
| `SurfaceList` | Camera optics with proper material TER files |
| `TERCurve` | Lens material transmission curves |
| `FilterWheel` | Already working, no changes |
| `ChopNodCombiner` | LM-band chop-nod background subtraction |
