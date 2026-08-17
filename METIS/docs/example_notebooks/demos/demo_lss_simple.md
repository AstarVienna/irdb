---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.5
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Simulating long-slit spectroscopy in METIS
This notebook shows the most basic setup for long-slit spectroscopy, using a star as the source.

```{code-cell} ipython3
import numpy as np
from matplotlib import pyplot as plt

import scopesim as sim
sim.bug_report()

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.link_irdb("../../../../")
```

If you haven't got the instrument packages yet, uncomment the following cell.

```{code-cell} ipython3
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

Set up the instrument in lss_l mode:

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["lss_l"])
```

```{code-cell} ipython3
metis = sim.OpticalTrain(cmd)
```

The source is a star with Vega spectrum and apparent brightness of 12 mag.

```{code-cell} ipython3
src = sim.source.source_templates.star(flux=12)
```

```{code-cell} ipython3
metis.observe(src, update=True)
result = metis.readout(detector_readout_mode="auto", exptime=1)[0]
```

```{code-cell} ipython3
plt.figure(figsize=(12,10))
plt.imshow(result[1].data, origin="lower", vmin=100, norm="log")
plt.colorbar();
```

## Rectifying the spectrum
The default configuration for METIS applies a non-linear mapping of the two-dimensional spectrum onto the detector as determined from ray-tracing simulations of the optical system. The mapping can be reversed to obtain a rectified version of the 2D spectrum that is linear in both wavelength and spatial position and can easily be analysed. Note that this is optimistic compared to an actual data reduction process, where the mapping parameters would have to be estimated from data with some uncertainty.

```{code-cell} ipython3
tracelist = metis["spectral_traces"]
```

```{code-cell} ipython3
rectified = tracelist.rectify_traces(result, -4, 4)
```

`rectified` is again an `HDUList` with the data in the first extension. The header of this extension contains the WCS keywords needed to translate from pixels to wavelength and spatial position.

```{code-cell} ipython3
from astropy.wcs import WCS
from astropy import units as u
wcs = WCS(rectified[1].header)
naxis1, naxis2 = wcs._naxis
det_wave = wcs.all_pix2world(np.arange(naxis1), 1, 0)[0] * u.Unit(wcs.wcs.cunit[0])
det_xi   = wcs.all_pix2world(1, np.arange(naxis2), 0)[1] * u.Unit(wcs.wcs.cunit[1])
det_wave = det_wave.to(u.um).value   # ensure desired units and dismiss for plotting
det_xi   = det_xi.to(u.arcsec).value
```

```{code-cell} ipython3
plt.figure(figsize=(12,7))
plt.imshow(rectified[1].data, vmin=100, norm="log",
           extent=(det_wave[0], det_wave[-1], det_xi[0], det_xi[-1]),
           origin="lower", aspect="auto")
plt.xlabel(r"Wavelength [$\mu$m]")
plt.ylabel("Position along slit [arcsec]")
plt.colorbar();
```
