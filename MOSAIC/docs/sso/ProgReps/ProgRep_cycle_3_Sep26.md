## [[sso-etc:Cycle_3|ETC - Cycle 3]]

### Summary

Cycle 3 closes both of the items left open at the end of cycle 1. The three
near-infrared mIFU modes are released, taking MOSAIC from nine to twelve working
observing modes, and the question of how fibre-resolved data should reach the
science user is answered by a new `MosaicOutputFormat` effect in ScopeSim: the
mIFU readout is a FITS binary table with one row per fibre, carrying each fibre's
position on sky alongside its spectrum. The demo notebook has been extended with a
full mIFU walkthrough and with two cross-checked recipes for estimating
signal-to-noise, and the MOSAIC documentation has been rebuilt on the new
ReadTheDocs theme.

All twelve modes have been verified to build and to produce a readout. The main
caveat for users is that `MosaicOutputFormat` has not yet appeared in a ScopeSim
release, so the package needs ScopeSim installed from `main` until v0.12.0 is out.
The work remaining is mostly calibration rather than functionality: the mIFU
bundles still carry 452 fibres rather than 169, the near-infrared detector
parameters are still inherited from MICADO, and MOSAIC has no automated test suite
of its own.

###  Status of the software ETC

There are still no deliveries expected for ESO. We continue to configure the
ScopeSim observation simulator for the MOSAIC science team to run feasibility
studies for their science cases.

The two reference documents are unchanged since cycle 1:

Slide deck with status as of Dec 2025: https://docs.google.com/presentation/d/1ETeuM7kiLp1xcO7O2RYnMYhZ6aWak1xdJuDS0vtABWE/edit?usp=sharing

First draft of the ETC specifications document for ESO: https://docs.google.com/document/d/1cWhtF89n1mRFJ9IDOIE9Syhfm56tR6-5YGoQeVHBBD0/edit?usp=sharing

In this cycle both items listed as open at the end of
cycle 1 have been addressed: the **mIFU modes are released**, and the **question of
how fibre-resolved data is handed to the science user has been answered** by a new
output-format layer in ScopeSim.

#### Functionalities implemented

The MOSAIC package in the ScopeSim "Instrument Reference Database" (IRDB):
* ReadTheDocs: https://irdb.readthedocs.io/en/latest/MOSAIC/docs/README.html
* Demo Notebook: https://github.com/AstarVienna/irdb/blob/dev_master/MOSAIC/docs/example_notebooks/MOSAIC_demo.ipynb

Twelve observing modes are now defined (the mIFU modes are new this cycle):

| Arm | Family | Modes |
|-----|--------|-------|
| VIS | MOS-LR  | B, R |
| VIS | MOS-HR  | B1, B2, R1, R2 |
| NIR | MOS-LR  | J, H |
| NIR | MOS-HR  | H |
| NIR | mIFU-LR | J (new), H (new) |
| NIR | mIFU-HR | H (new) |

Cycle 1 reported the NIR MOS modes as the combined entries "MOS-LR-J+H" and
"MOS-HR-H"; they are listed individually here, which is how they are selected in
the package. The genuinely new modes this cycle are the three mIFU modes.

Bundle geometry, as carried in the trace files:
* MOS-LR: 7 fibres of 0.218 arcsec, bundle approx. 0.68 arcsec across
* MOS-HR: 19 fibres
* mIFU: 452 fibres of 0.140 arcsec, bundle approx. 1.9 x 1.7 arcsec

The MOSAIC package in ScopeSim makes use of the following optical effect
descriptions:
  1. ADConversion
  2. AutoExposure
  3. BasicReadoutNoise
  4. DarkCurrent
  5. DetectorList
  6. ExposureIntegration
  7. ExposureOutput
  8. LinearityCurve
  9. LineSpreadFunction
  10. MetisLMSImageSlicer (repurposed for MOSAIC)
  11. **MosaicOutputFormat** (new - replaces MosaicCollapseSpectralTraces)
  12. MosaicSpectralTraceList
  13. QuantumEfficiencyCurve
  14. ReferencePixelBorder
  15. SeeingPSF
  16. ShotNoise
  17. TERCurve

##### Output formats

`MosaicCollapseSpectralTraces` has been generalised into `MosaicOutputFormat`,
which is set per mode through the `output_format` property in
`MOSAIC/default.yaml`:

* `collapse1d` - all fibres in the bundle are summed into a single spectrum. The
  readout is a FITS binary table with columns `wavelength` and `spectrum`. This is
  the default for all nine MOS modes.
* `table` - one row per fibre, with columns `id`, `x`, `y`, `wavelength`,
  `spectrum`. `x` and `y` give the on-sky position of the fibre relative to the
  bundle centre; `wavelength` and `spectrum` are arrays. This is the default for
  the three mIFU modes, and is the answer to the cycle-1 open question about how
  mIFU data should be made available to the science user. It is sufficient for a
  crude image reconstruction by colour-coding the fibre positions by integrated
  flux, which the demo notebook now demonstrates.
* `image` - a pseudo-detector image with one row per fibre spectrum. Declared but
  **not yet implemented** (currently a no-op).

Because the format is a per-mode property it can be overridden by the user, e.g.
to obtain the individual fibre spectra of a MOS bundle rather than the collapsed
sum.

Verified end to end in this repository against ScopeSim `main`:

| Mode | Image plane | Readout | Wall clock |
|------|-------------|---------|------------|
| MOS-LR-R  | 160 x 13000 | BinTableHDU, 13000 rows, `wavelength` / `spectrum` | approx. 16 s |
| mIFU-LR-J | 4096 x 4096 | BinTableHDU, 452 rows, `id` / `x` / `y` / `wavelength` / `spectrum` | approx. 42 s |
| mIFU-HR-H | 4096 x 4096 | BinTableHDU, 452 rows, 4096 spectral samples over 1.523 - 1.621 um | approx. 60 s |

All twelve modes were checked to build; the three above were additionally run
through `observe()` and `readout()` on a 15 mag star.

##### Signal-to-noise ratio

Cycle 1 listed a standardised way of estimating SNR as a task for the next cycle.
ScopeSim still has no built-in SNR function, but the demo notebook now documents
two consistent recipes and shows that they agree:

1. **Empirical** - simulate blank sky and source+sky with the same exposure time,
   subtract, and take the noise from the source+sky readout scaled by the gain.
2. **From expected values** - use the noise-free `ImagePlane` of both simulations
   and apply the ELT Spectroscopy ETC prescription
   (https://www.eso.org/observing/etc/doc/elt/etc_spec_model.pdf):
   S/N = sqrt(n_exp) * N_obj / sqrt(N_obj + N_sky + n_pix * (R^2 + D*t)),
   with n_pix the number of fibres summed over.

The detector noise values entering this are R = 7 e- and D = 0.005 e-/s per fibre
for the VIS arm, scaled from the 2.5 e- and 3 e-/hr/pixel quoted in
E-MOS-SYS-ANR-0063-2_0 assuming approximately 6 detector pixels per fibre.

##### Documentation

The MOSAIC documentation was rebuilt as part of the IRDB-wide documentation
overhaul (May 2026): ReadTheDocs moved to sphinx-book-theme + myst-nb, all
instrument pages are now Markdown, and the MOSAIC page links to a shared ScopeSim
user guide instead of repeating the ScopeSim basics. MOSAIC has a landing-page card
and an entry in the instrument table on the IRDB front page. The demo notebook is
executed by the `notebooktests` CI workflow on every change.

#### Limitations

Known issues, ordered by how much they affect a science user:

1. **`MosaicOutputFormat` is not in any released ScopeSim.** The latest release is
   v0.11.4 (19 May 2026); the effect was merged to `main` on 7 Aug 2026 and will
   appear in v0.12.0. `MOSAIC/default.yaml` still declares
   `needs_scopesim: "v0.11.0"`. Until v0.12.0 is out the package requires ScopeSim
   installed from `main`.
2. **The mIFU bundles still contain 452 fibres.** A reduction to 169 fibres exists
   on the `oc/mosaic_update` branch (Oct 2025) but was never merged, and that branch
   is now 238 commits behind `dev_master`. The change has to be re-applied on top of
   the current trace files.
3. **The `image` output format is a stub** and silently returns its input unchanged.
4. **There is no automated test suite for MOSAIC.** `MOSAIC/tests/` is empty and the
   package is only exercised through the demo notebook in CI. Other IRDB packages
   (MICADO, METIS, MAVIS) carry pytest suites that validate throughput and radiometry
   against published numbers; MOSAIC should get the equivalent.
5. **Detector parameters are still estimates.** The NIR arm uses gain 2.5 e-/ADU,
   dark current 0.05 e-/s and read noise 12 e-, carried over from the MICADO H4RG and
   marked "conservative" / "estimate" in the yaml. All twelve modes carry
   `status: development`.
6. **The detector gap is not simulated.** The VIS arm is modelled as a single
   13000-pixel pseudo-detector; the gap between the two 6k CCDs of the real
   instrument is ignored.
7. **No GLAO PSF.** Delivered image quality is a `SeeingPSF` of fixed FWHM
   (`!OBS.psf_fwhm`, default 0.2 arcsec). The hooks for a `psf_file` are in place but
   commented out.
8. **No aperture losses beyond the fibre geometry** and no fibre-to-fibre variation
   in throughput.

###  Version of the software
* ScopeSim for MOSAIC v0.2
* ScopeSim: https://github.com/AstarVienna/ScopeSim (requires `main`, towards v0.12.0)
* MOSAIC instrument package: https://github.com/AstarVienna/irdb/tree/dev_master/MOSAIC

### Development incrementation

#### New features
* Three mIFU modes released (mIFU-LR-J, mIFU-LR-H, mIFU-HR-H), bringing the package
  to twelve modes; the mIFU trace files carry 452 fibre apertures each
* New ScopeSim effect `MosaicOutputFormat`, generalising the cycle-1
  `MosaicCollapseSpectralTraces` into a per-mode selectable output format
  (`collapse1d` / `table` / `image`)
* Fibre-resolved `table` output: a FITS binary table with one row per fibre,
  including the on-sky fibre positions, which enables crude image reconstruction
* `output_format` exposed as an OBS property so it can be overridden per run
* Demo notebook extended with a full mIFU walkthrough (fibre table, fibre-position
  plot, extraction of a single fibre spectrum) and with two documented SNR recipes
* MOSAIC documentation rebuilt in Markdown on the new ReadTheDocs theme, with a
  landing-page card and a shared ScopeSim user guide

#### Bug corrections
* `mIFU-HR-H` could not be built: `MOSAIC/default.yaml` referenced
  `TER_spec_NIR_HR_H.dat` and `TRACE_mIFU_NIR-HR-H.fits`, while the files shipped in
  the package are `TER_spec_HR-H.dat` and `TRACE_mIFU-HR-H.fits`, so constructing the
  optical train failed with `ValueError: Empty filename: None`. The two filenames
  have been corrected and all twelve modes now build and read out.
* `ReferencePixelBorder` updated to follow a ScopeSim API change
* Demo notebook corrected to account for ScopeSim issue #962

### functionalities to be implemented in the next cycle
* Update `needs_scopesim` once ScopeSim v0.12.0 is released, and re-check that the
  package runs against the release rather than against `main`
* Re-apply the reduction of the mIFU bundles from 452 to 169 fibres
* Implement the `image` output format
* Add a pytest suite for MOSAIC, in line with the MICADO / METIS / MAVIS packages,
  validating system throughput and background levels against the MOSAIC reference
  documents
* Wrap the SNR recipes documented in the notebook into a standardised helper, and
  extend it to the per-line SNR estimate already requested in cycle 1
* Replace the fixed-FWHM `SeeingPSF` with a GLAO PSF once one is available
* Replace the estimated NIR detector parameters with MOSAIC-specific values
