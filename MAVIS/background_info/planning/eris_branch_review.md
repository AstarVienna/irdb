# Review of `kl/eris_nix_basic`

Reviewed 2026-08-30 against `dev_master` at 23e168b, in a throwaway worktree.
Filed here because the branch itself has no review notes; move it to
`ERIS/background_info/` if that branch is picked up.

## Verdict

Good work that is **not mergeable as it stands** — not because of the physics,
which is solid, but because of five integration problems, two of which are
outright bugs. None is hard to fix.

## What the branch contains

Two commits, ~39k lines:

- **`ERIS/`** — NIX imager. Four AO-mode yamls (NGS / LGS / SE / NOAO), an
  H2RG detector, three imaging modes (JHK-13mas, JHK-27mas, LM-13mas),
  18 filter curves, material TER curves, and a test suite validating against
  Davies et al. 2023 throughput numbers.
- **`HAWKI_new/`** — a rebuilt HAWKI sitting alongside the existing `HAWKI/`,
  with tests comparing old against new.
- **`ERIS/background_info/planning/`** — staged implementation plans
  (step2 optics/filters, step3 special modes, step4 TipTop PSF, phase2
  SPIFFIER IFU). These are good and are the model the MAVIS planning
  documents in this directory follow.

## Test results

| Suite | Result |
|---|---|
| `ERIS/tests/` | 34 passed |
| `HAWKI_new/tests/` | 38 passed |
| `irdb/tests/test_package_contents.py -m badges` | **2 failed** — ERIS and HAWKI_new |

## Findings

### 1. NDIT does nothing — `ExposureOutput` averages where the yaml says sum

`ERIS/ERIS_NIX_H2RG.yaml:87` declares

```yaml
  - name: exposure_output
    description: return sum over NDIT sub-exposures
    class: ExposureOutput
```

with no `kwargs`, so the effect takes its default `mode: average`. Measured
on an empty-sky readout:

```
dit=60 ndit=1  median = 408.2
dit=60 ndit=4  median = 408.4     ratio 1.0005, expected 4
```

The description and the behaviour disagree. `MICADO/MICADO_H4RG.yaml:85`
sets `mode: sum` explicitly; MAVIS hit the same trap and now does too. Same
issue in `HAWKI_new/HAWKI_H2RG.yaml:83`.

**Fix:** add `kwargs: {mode: sum}`, or change the description if averaging is
intended. Add a test that NDIT scales the signal.

### 2. Two PSFs are convolved together

The built ERIS train carries both:

```
('VLT', 'vlt_generic_psf')      FieldConstantPSF   <- from VLT.yaml
('ERIS_AO_NGS', 'eris_ao_psf')  SeeingPSF
```

so the AO PSF is broadened a second time by the VLT poppy PSF. MAVIS had the
identical problem.

**Fix:** the `kl/mavis` branch adds `!TEL.include_generic_psf` to
`VLT/VLT.yaml` (defaulting to `True`, so nothing else changes) and switches it
off in a TEL-aliased override document at the end of `MAVIS/MAVIS.yaml`. ERIS
can use the same switch once the branches meet. Whichever branch merges first
should carry the `VLT.yaml` change.

### 3. Both packages fail the structure badge test

`irdb/tests/test_package_contents.py::test_default_yaml_contains_packages_list`
requires a top-level `yamls:` list in `default.yaml` containing
`<PKG>.yaml`, for every package except METIS and MOSAIC.

- **ERIS** — `default.yaml` has `packages:` and `mode_yamls:` but no base
  `yamls:`.
- **HAWKI_new** — has a `yamls:` list, but the test looks for
  `HAWKI_new.yaml` and the file is `HAWKI/HAWKI.yaml`. The directory name and
  the self-named yaml disagree.

**Fix for ERIS:** add a base `yamls:` with only what all modes share.
**Watch out:** anything listed both in the base list and in a mode's `yamls:`
loads twice, duplicating every optical element and squaring the system
throughput. That is exactly what happened on `kl/mavis` (fixed in b303338,
regression test `TestRadiometry::test_effects_are_not_applied_twice`). ERIS's
mode yamls currently repeat `Paranal.yaml`, `VLT.yaml` and `ERIS.yaml` in
each of the four AO modes, so a naive base list would duplicate all three.

**Fix for HAWKI_new:** decide the name first — see finding 5.

### 4. Neither package is registered for publishing

`irdb/server_folders.yaml` lists neither `ERIS` nor `HAWKI_new`, so neither
would be published to the package server.

### 5. `HAWKI_new/` duplicates `HAWKI/` — a policy decision, not a bug

The repo now carries two HAWKI packages with overlapping filters, detector
files and yamls. `HAWKI_new/tests/` contains both `test_hawki_new.py` and
`test_hawki_original.py`, which is a sensible way to justify a replacement
but not a sensible thing to ship. This needs a maintainer decision:

- replace `HAWKI/` with the new package and keep the name `HAWKI`, or
- drop `HAWKI_new/` from the branch and land ERIS alone, or
- keep both, which means naming, registering and documenting both.

Landing ERIS on its own is the smallest useful merge and is what I would
suggest; the HAWKI rebuild can be its own PR with its own argument.

### 6. Docs predate the documentation overhaul

The branch is 41 commits behind `dev_master`, which merged PR #347
(sphinx-book-theme + myst-nb, Markdown docs).

- `ERIS/docs/readme.rst` needs to become `ERIS/docs/README.md`.
- `HAWKI_new/docs/` has no readme at all.
- Neither package appears in the `index.md` table or toctree.
- `dev_master` already has an `ERIS/` directory holding `readme.md` and two
  PDFs; the branch keeps `ERIS/readme.md` at the package root *and* adds
  `ERIS/docs/readme.rst`. Pick one location.

## Merge mechanics

`git merge dev_master` into the branch is **clean — no conflicts.** The work
is bringing the docs up to the new layout, not resolving textual conflicts.

## What is good and should not be changed

- Filter provenance is careful. `ERIS/filters/*.dat` record the SVO filter
  ID (`Paranal/ERIS.K` and friends), and I checked those profiles are
  `components = Filter`, so the separately applied `QE_H2RG_5um.dat` is not
  double-counted. `HAWKI_new` filters are also filter-only but their headers
  omit the `svo_id`, which is worth adding.
- Validating against published throughput (Davies+2023: 42 % J, 61 % H,
  52 % K) is the right instinct and matches how MAVIS is now validated.
- The staged planning documents are genuinely useful and are the format
  worth standardising on.

## Suggested order of work

1. Merge `dev_master` in (clean).
2. Fix `ExposureOutput` `mode: sum`, with a DIT/NDIT regression test.
3. Decide the HAWKI question; if dropping, remove `HAWKI_new/` from the
   branch.
4. Add the base `yamls:` to `ERIS/default.yaml`, being careful not to
   duplicate entries already in the mode lists, and add the duplication
   regression test.
5. Register ERIS in `irdb/server_folders.yaml`.
6. Port the docs to `ERIS/docs/README.md` and add ERIS to `index.md`.
7. Take the `!TEL.include_generic_psf` switch from `kl/mavis` (or add it, if
   that branch has not landed) and disable the VLT PSF for ERIS.
