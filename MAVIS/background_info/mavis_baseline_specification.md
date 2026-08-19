# MAVIS — baseline specification and reference notes

Reference notes compiled for the ScopeSim MAVIS package. Numbers here are the source
of truth for the values that appear in the package YAML and `.dat` files.

Sources (retrieved 2026-08-19; text extracted from locally saved copies of the pages,
which have since been discarded in favour of these notes):

| Ref | Source | Page last updated |
|---|---|---|
| **[ESO]** | ESO instrument page — <https://www.eso.org/sci/facilities/paranal/instruments/mavis.html> | 2025-11-12 |
| **[MAVIS-A]** | MAVIS consortium "About" page — <https://mavis-ao.org/mavis/about/> | Phase A snapshot |
| **[MAVIS-R]** | MAVIS consortium "Resources" page — <https://mavis-ao.org/mavis/resources/> | 2018-06-14 (v0.9) |

Where **[ESO]** and **[MAVIS-A]** disagree, **[ESO]** wins — it is the current baseline,
whereas the consortium About page still carries phase-A goal values.

## Project status

- Instrument approved by ESO December 2020; Final Design Review (Phase B) stage. **[ESO]**
- Consortium: INAF (Osservatorio Astronomico di Padova / Capodimonte), Australian National
  University / AAO-Macquarie, Laboratoire d'Astrophysique de Marseille, ESO. **[ESO]**
- Location: **Nasmyth A of VLT UT4 (Yepun)**, on the Adaptive Optics Facility, opposite
  MUSE. **[ESO]**

### Schedule **[ESO]**

| Milestone | Date |
|---|---|
| Phase A study review | 2020-05-26 (completed) |
| ESO project approval | 2020-12 (completed) |
| Preliminary Design Review (PDR) | 2023 (completed) |
| Long Lead Items Review (LLI) | 2023 (completed) |
| Final Design Review (FDR) | 2025-10 |
| Preliminary Acceptance Europe (PAE/A) | 2030 |
| **First light at the telescope** | **2031** |

> Note: an earlier version of this package's docs said "first light around 2027". That is
> wrong — the current ESO baseline is 2031.

## General properties and AO module **[ESO]**

| Parameter | Value |
|---|---|
| Focus | Nasmyth A, VLT-AOF (UT4) |
| Science field of view | 30″ × 30″ |
| NGS field of view | 120″ diameter disk |
| Number of NGS | up to 3 (tip-tilt) |
| LGS beacons | **up to 8**, on a circle of 17.5″ diameter |
| Deformable mirrors | AOF deformable secondary + post-focal DMs (MCAO) |
| Strehl (V band) | **> 8 %** (goal 12 %) |
| Ensquared energy | > 15 % within 50 mas at 550 nm |
| Sky coverage | ⩾ 50 % at the South Galactic Pole |
| NGS limiting magnitude | H ⩾ 18.5 |
| Point-source sensitivity | **V > 29 mag (5σ) in 1 hr** |
| Angular resolution | down to ~18 mas |

> **LGS count caveat.** **[ESO]** gives *up to 8* LGS. The publicly released LAM PSF
> simulations (see below) and MAVISIM were run with **5 LGS + 3 DM**. When citing a PSF,
> state which configuration it came from. An earlier version of this package's docs said
> "up to 5 LGS on a 17.5″ ring", conflating the simulation setup with the instrument
> baseline.

> **Strehl caveat.** **[MAVIS-A]** (phase A) quotes "> 10 % (15 % goal)". **[ESO]**
> (current) quotes "> 8 % (12 % goal)". The package uses the ESO values.

## Imager **[ESO]**

| Parameter | Value |
|---|---|
| Pixel scale | 7.36 mas/pix |
| Field of view | 30″ × 30″ |
| Filters | u′ g′ r′ i′ z′, plus various narrow bands |

> **Filter caveat.** **[ESO]** lists only the SDSS set plus narrow bands. **[MAVIS-A]**
> (phase A) lists "BVRI, ugriz, various narrow bands". The package currently ships both
> Bessel/Cousins BVRI and SDSS u g r i z; the SDSS set is the one on the current ESO
> baseline, so treat BVRI as convenience filters rather than as confirmed hardware.

## IFU spectrograph **[ESO]**

Not yet implemented in this ScopeSim package.

| Parameter | Value |
|---|---|
| Spaxel + FoV, fine | 20–25 mas spaxels, 2.5″ × 3.6″ FoV |
| Spaxel + FoV, coarse | 40–50 mas spaxels, 5″ × 7.2″ FoV |

Spectral configurations:

| Config | Resolving power R = λ/Δλ | Wavelength range |
|---|---|---|
| LR-Blue | 5 900 | 370–720 nm |
| LR-Red | 5 900 | 510–935 nm |
| HR-Blue | 14 700 | 425–550 nm |
| HR-Red | 11 500 | 630–880 nm |

**[MAVIS-A]** (phase A) additionally quotes per-config limiting magnitudes and a slightly
different LR-Red range (510–1000 nm): LR-Blue 21 @ 550 nm, LR-Red 21.5 @ 750 nm,
HR-Blue 19.6 @ 475 nm, HR-Red 20.7 @ 725 nm.

## PSF simulations **[MAVIS-R]**

Provided by Benoit Neichel, Thierry Fusco, Yoan Brule (Laboratoire d'Astrophysique de
Marseille). Preliminary; not a full end-to-end model.

- **Configuration:** 5 LGS, 3 DMs, monochromatic at 500 / 700 / 900 nm.
- **Field size:** 30″ × 30″ effective.
- **Input catalogue:** stellar magnitudes designed to give a stated effective surface
  brightness at 3.5 Mpc, for a stellar population with an exponentially decaying SFR
  (3 Gyr e-folding time).
- **Sampling:** originals at 2× critical sampling of the VLT diffraction limit (so pixel
  scale varies with wavelength); rebinned versions adopt **7.5 mas pixels**, giving
  4k × 4k images over the 30″ field.

Available datasets (sizes are the download sizes of the FITS products, which are *not*
bundled here):

| Effective surface brightness | 500 nm | 700 nm | 900 nm |
|---|---|---|---|
| 26 mag/arcsec² (original) | 625 MB | 323 MB | 196 MB |
| 22 mag/arcsec² (original) | — | 313 MB | — |
| 26 mag/arcsec² (rebinned 7.5 mas) | 62 MB | 62 MB | — |

Preview images of these fields are in `figures/lam_psf_*.png`.

> Note the LAM rebinned pixel scale is **7.5 mas**, not the 7.36 mas/pix of the imager —
> resample before use as a `FieldConstantPSF`/`FieldVaryingPSF`.

## Imaging point-source sensitivity assumptions **[MAVIS-R]**

From Esposito et al. 2016, Proc. SPIE 9909, 99093U — an optical MCAO system like MAVIS.
Useful as an order-of-magnitude cross-check for the radiometry tests.

| Assumption | HST/ACS-WFC | VLT |
|---|---|---|
| Source flux for R = 25 | 2 ph/s | **20 ph/s** |
| Background flux | 35 ph/arcsec²/s | **846 ph/arcsec²/s** |
| Plate scale | 50 mas | **10 mas** |
| Read noise | 4 e⁻/pix | **2 e⁻/pix** |
| Throughput | ~0.4 (F625W) | **~0.3 (VIMOS R)** |

SNR estimated with the standard formula

```
SNR = gamma_source / sqrt( gamma_source + gamma_bck * rho^2 + sigma_RON^2 * n_pix )
```

See `figures/snr_vs_aperture_esposito2016.png`.

> The ~0.3 total throughput figure is for VIMOS in R, used as a stand-in. It is a
> reasonable sanity bound for the MAVIS total (telescope + AO module + filter + QE) but
> is **not** a MAVIS measurement.

## Key literature

- **Science case:** <https://arxiv.org/abs/2009.09242>
- **MAVISIM** image simulator: Monty et al. 2021, MNRAS 507, 2192 —
  <https://github.com/smonty93/mavisim>
- Esposito et al. 2016, Proc. SPIE 9909, 99093U — optical MCAO sensitivity
- Pallottini et al. 2017 — the "Althaea" z = 5 simulated galaxy used in the ESO
  morphology comparison figure
- ESO Top Level Requirements (TLRs) — public, on the ESO website

## Figures kept in `figures/`

| File | Content | Source |
|---|---|---|
| `lam_psf_sb26_5lgs_3dm_{500,700,900}nm.png` | LAM MCAO simulated fields, 26 mag/arcsec², native sampling | [MAVIS-R] |
| `lam_psf_sb22_5lgs_3dm_700nm.png` | as above, 22 mag/arcsec² | [MAVIS-R] |
| `lam_psf_*_rebin7.5mas.png` | same fields rebinned to 7.5 mas pixels | [MAVIS-R] |
| `snr_vs_aperture_esposito2016.png` | SNR vs aperture, Esposito et al. 2016 | [MAVIS-R] |
| `ao_loop_diagram.png` | single-conjugate AO loop schematic | [MAVIS-A] |
| `mcao_principle.gif` | MCAO tomography schematic | [MAVIS-A] |
| `mavis_at_nasmyth.png` | MAVIS on the UT4 Nasmyth A platform | [MAVIS-A] |
