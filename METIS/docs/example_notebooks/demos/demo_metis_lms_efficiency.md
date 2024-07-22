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

# Demonstration of METIS LMS Efficiency

This notebook demonstrates the effect `MetisLMSEfficiency`. Here we use it standalone to reproduce Figure 6 from E-REP-ATC-MET-1016 (v1.0) to show that the effect computes the efficiency correctly.

```{code-cell} ipython3
import numpy as np
from astropy import units as u
from matplotlib import pyplot as plt

import scopesim as sim
from scopesim.effects.metis_lms_trace_list import MetisLMSEfficiency

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../../"
```

If you haven't got the instrument package yet, uncomment the following cell. The METIS package provides the spectral trace definition file. The ELT and Armazones packages are not needed for the purposes of this notebook.

```{code-cell} ipython3
# sim.download_packages(["METIS"])
```

When simulating an LMS observation, the user selects a target wavelength by setting `cmd['!OBS.wavelen']`, e.g. 4.2 (microns). In normal use, the efficiency is instantiated as an effect within the `OpticalTrain`. Here, we instantiate the effect directly as

```{code-cell} ipython3
eff = MetisLMSEfficiency(wavelen=4.2, filename="../../../TRACE_LMS.fits")
```

The effect automatically selects the echelle order for that wavelength and computes the grating efficiency.

```{code-cell} ipython3
print(eff.meta['order'])
```

```{code-cell} ipython3
eff.surface.transmission.plot()
```

Alternatively, the order can be specified directly. This is used in the following to plot the efficiencies for all orders. The resulting figure can be compared to the original figure from E-REP-ATC-MET-1016.

```{code-cell} ipython3
plt.figure(figsize=(8, 6))
plt.ylim(0, 1)
plt.xlim(3.0, 5.05)
plt.xlabel(r"Wavelength [$\mathrm{\mu m}$]")
plt.ylabel("Efficiency")
plt.xticks(np.arange(3.0, 5.05, 0.2))
for order in np.arange(22, 37):
    eff = MetisLMSEfficiency(order=order, filename="../../../TRACE_LMS.fits")
    lam = eff.surface.transmission.waveset
    effic = eff.surface.transmission(lam)
    lammax = lam[np.argmax(effic)]
    p = plt.plot(lam.to(u.um), eff.surface.transmission(lam))
    plt.text(lammax.to(u.um).value, 0.76, str(order), ha='center', color=p[0].get_color())
```

```{code-cell} ipython3

```
