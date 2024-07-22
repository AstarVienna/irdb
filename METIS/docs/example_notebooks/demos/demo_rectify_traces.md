---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# How to obtain wavelength-calibrated and rectified 2D spectra

This notebook demonstrates how to rectify a detector readout from a spectroscopic simulation using Scopesim. "Rectification" means the transformation of a spectral trace from the detector onto a rectangular pixel grid of wavelength and spatial position along the slit. Wavelength calibration and rectification are major tasks of the spectroscopic data-reduction pipeline. For convenience, Scopesim includes functionality to perform these tasks by reversing the *known* mapping that was used for the simulation, resulting in easily analysable 2D spectra that include all the noise and background components but neglect the uncertainties of a wavelength calibration as it would be performed during the reduction of real data. 
Rectification is demonstrated on a METIS long-slit simulation, but the procedure applies to MICADO spectroscopic simulations as well (but more expensive to simulate and rectify). METIS IFU simulations have to be treated differently.

```{code-cell} ipython3
import numpy as np
from matplotlib import pyplot as plt

from astropy import units as u
from astropy.wcs import WCS

from synphot import SourceSpectrum, Empirical1D
from scopesim_templates.micado import flatlamp
import scopesim as sim
```

```{code-cell} ipython3
# Edit this path if you have a custom install directory, otherwise comment it out.
sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../../"
```

If you haven’t got the instrument packages yet, uncomment the following cell.

```{code-cell} ipython3
# sim.download_package(["METIS", "ELT", "Armazones"])
```

## Creation of a source - lamp with equally spaced lines

As an example, we use a calibration lamp with equally spaced and equally strong emission lines, covering the L band. The line list is turned into a spectrum by placing a narrow Gaussian at each line position. To simulate the lamp, we (ab)use the `flatlamp` function and replace the default spectrum (a black body) by the line spectrum.

```{code-cell} ipython3
lines = np.arange(2.8, 4.2, 0.1)

wave = np.linspace(2.8, 4.2, 4096)
flux = np.zeros_like(wave)
sigma = 0.0005
for line in lines:
    flux += 0.0003 * np.exp(-(wave - line)**2 / (2 * sigma**2))

spec = SourceSpectrum(Empirical1D, points=wave*u.um, lookup_table=flux)

src_linelamp = flatlamp()
src_linelamp.fields[0].spectra[0] = spec
```

## Simulation of an observation

We use METIS in the L-band long-slit spectroscopic mode, using a fairly narrow slit. We explicitely request the realistic spectral mapping with non-linear dispersion.

```{code-cell} ipython3
cmds = sim.UserCommands(use_instrument="METIS", set_modes=["lss_l"],
                       properties={"!OBS.trace_file": "TRACE_LSS_L.fits",
                                   "!OBS.slit": "B-28_6"})

metis = sim.OpticalTrain(cmds)
```

We exclude atmospheric emission (and absorption) as is appropriate for a calibration-lamp observation. As the source fills the slit homogeneously a PSF convolution should have no effect on the result. Excluding PSF convolution cuts down significantly on computation time.

```{code-cell} ipython3
:tags: [hide-output]

metis["skycalc_atmosphere"].include = False
metis["psf"].include = False

metis.observe(src_linelamp, update=True)
```

```{code-cell} ipython3
readout = metis.readout(exptime=5, dit=None, ndit=None)[0]

plt.imshow(readout[1].data, origin="lower")
plt.colorbar()
```

## Rectification of the spectrum

The non-linearity in the dispersion in METIS is small and not readily apparent. Still, rectification is necessary to arrive at a 2D spectrum with well-defined wavelength and spatial coordinates. The method to use is `rectify_traces` and belongs to the `SpectralTraceList` effect, which is accessible in the METIS `OpticalTrain` as `"spectral_traces"` (in MICADO it would be `"micado_spectral_traces"`. Currently, it is necessary to specify the spatial extent of the slit when calling the method. The long slit in METIS has a length of 8 arcsec and extends from -4 arcsec to +4 arcsec.

```{code-cell} ipython3
tracelist = metis["spectral_traces"]
rectified = tracelist.rectify_traces(readout, -4.0, 4.0)
```

`rectified` is a HDU list with one extension for each spectral trace - for METIS there's only one trace, for MICADO there would be several. Each extension has a WCS that translates pixel coordinates into wavelength and position along the slit.

```{code-cell} ipython3
wcs = WCS(rectified[1])
naxis1 = rectified[1].header["NAXIS1"]
naxis2 = rectified[1].header["NAXIS2"]
```

```{code-cell} ipython3
lam = (wcs.all_pix2world(np.arange(naxis1), 800, 0)[0] * u.Unit(wcs.wcs.cunit[0])).to(u.um).value
xi = (wcs.all_pix2world(1000, np.arange(naxis2), 0)[1] * u.Unit(wcs.wcs.cunit[1])).to(u.arcsec).value
```

```{code-cell} ipython3
plt.imshow(rectified[1].data, origin="lower", extent=[lam[0], lam[-1], xi[0], xi[-1]])
plt.gca().set_aspect("auto")
plt.xlabel(r"Wavelength [$\mathrm{\mu m}$]")
plt.ylabel(r"Spatial position along slit [arcsec]");
```

```{code-cell} ipython3
i1, i2 = 120, 620
plt.figure(figsize=(12, 6))
plt.plot(lam[i1:i2], rectified[1].data[800, i1:i2], label="single row")
plt.plot(lam[i1:i2], rectified[1].data.mean(axis=0)[i1:i2], label="average")
plt.legend()
plt.xlabel(r"Wavelength [$\mathrm{\mu m}$]");
```

```{code-cell} ipython3

```
