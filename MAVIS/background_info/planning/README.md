# MAVIS IFU spectrograph — implementation plan

MAVIS is an imager **and** an IFU spectrograph. This package currently
implements the imager only. These documents plan the spectrograph.

## Why this is planned rather than built

The imager was buildable because every number in it traces to a source: the
ESO baseline page, the consortium pages, FORS2 and SDSS filter measurements,
the VLT pupil geometry, and the MAVISIM end-to-end PSF.

For the spectrograph, the published material gives the **science parameters**
and nothing else:

| Published | Not published |
|---|---|
| Spaxel scales (20–25 mas fine, 40–50 mas coarse) | Number of slices, slice width |
| IFU fields of view (2.5″×3.6″, 5″×7.2″) | Detector format and count |
| Four spectral configs: R and wavelength range | Dispersion geometry, order layout |
| — | Whether the quoted range is simultaneous or tunable |
| — | Spectrograph throughput, grating efficiency |
| — | IFU detector noise, dark current, full well |

ScopeSim's dispersed-image IFU path (`MetisLMSImageSlicer` +
`SpectralTraceList` + a trace FITS) needs every item in the right-hand
column. Writing one would mean inventing the instrument, which is the
opposite of what this repository is for.

## The three steps

| Step | What | Blocked on consortium data? |
|---|---|---|
| [step1_ifu_cube_mode.md](step1_ifu_cube_mode.md) | Cube-output IFU modes via ScopeSim's simple-IFU path | **No** — buildable from published numbers today |
| [step2_ifu_slicer_and_traces.md](step2_ifu_slicer_and_traces.md) | Dispersed-image modes: slicer, spectral traces, detector layout | Yes |
| [step3_ifu_throughput_and_detectors.md](step3_ifu_throughput_and_detectors.md) | Spectrograph throughput, grating efficiency, detector characterisation | Yes |

**Step 1 does not depend on steps 2 and 3.** It is worth doing on its own:
it gives a usable ETC-grade IFU without a single invented geometric number.

## Source of the numbers

All instrument parameters quoted in these documents come from
[`../mavis_baseline_specification.md`](../mavis_baseline_specification.md),
which records where each one was taken from and where the current ESO
baseline disagrees with the phase-A figures. Do not copy numbers into the
YAML from these planning documents without checking them there first.
