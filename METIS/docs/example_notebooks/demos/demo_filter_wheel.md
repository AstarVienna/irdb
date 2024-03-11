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

# How to use the filter wheel(s)

This notebook demonstrates the use of the `FilterWheel` in Scopesim. The METIS configuration contains two instances of this effect, named `filter_wheel` (for science filters) and `nd_filter_wheel` (for neutral-density filters). Each filter wheel contains a number of predefined filters, with different filter sets for the LM- and N-band imagers. 

```{code-cell} ipython3
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

import scopesim as sim
sim.bug_report()

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../../"
```

If you haven't got the instrument packages yet, uncomment the following cell.

```{code-cell} ipython3
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=['img_lm'])
```

The filter to use is defined by setting `!OBS.filter_name`. In `img_lm` mode, it defaults to the Lp filter:

```{code-cell} ipython3
cmd['!OBS.filter_name']
```

```{code-cell} ipython3
metis = sim.OpticalTrain(cmd)
```

The METIS package defines the list of filters that are available in the real instrument:

```{code-cell} ipython3
metis['filter_wheel'].filters
```

At any moment one of these filters is in the optical path and used for the simulation. Initially, this is the one set by `!OBS.filter_name`:

```{code-cell} ipython3
metis['filter_wheel'].current_filter
```

The current filter can be changed to any of the filters in the list:

```{code-cell} ipython3
metis['filter_wheel'].change_filter("PAH_3.3")
metis['filter_wheel'].current_filter
```

## Observing the same source in different filters

```{code-cell} ipython3
src = sim.source.source_templates.empty_sky()

metis['filter_wheel'].change_filter("Lp")

metis.observe(src)
img_Lp = metis.image_planes[0].data

metis['filter_wheel'].change_filter("PAH_3.3")

metis.observe(src, update=True)
img_PAH = metis.image_planes[0].data

print(f"Background in Lp:      {np.median(img_Lp):8.1f} counts/s")
print(f"Background in PAH_3.3: {np.median(img_PAH):8.1f} counts/s")
```

## Using the neutral-density filter wheel

METIS also has neutral-density filters that can be inserted and changed using the `nd_filter_wheel` effect. The transmission of the filter `ND_ODx` is $10^{-x}$.

```{code-cell} ipython3
metis['nd_filter_wheel'].filters
```

```{code-cell} ipython3
metis['nd_filter_wheel'].current_filter
```

Observe a bright star (default arguments result in Vega at 0 mag) in the Lp filter. It will be found that the star saturates the detector in the open position, and requires the `ND_OD4` filter not to do so.

```{code-cell} ipython3
star = sim.source.source_templates.star()

metis['filter_wheel'].change_filter('Lp')
```

```{code-cell} ipython3
metis['nd_filter_wheel'].change_filter("open")
metis.observe(star, update=True)
hdu_open = metis.readout()[0][1]
```

```{code-cell} ipython3
metis['nd_filter_wheel'].change_filter("ND_OD3")
metis.observe(star, update=True)
hdu_OD3 = metis.readout()[0][1]
```

```{code-cell} ipython3
metis['nd_filter_wheel'].change_filter("ND_OD4")
metis.observe(star, update=True)
hdu_OD4 = metis.readout()[0][1]
```

```{code-cell} ipython3
plt.figure(figsize=(15, 4))
plt.subplot(131)
plt.imshow(hdu_open.data[700:1350, 700:1350], origin='lower', norm=LogNorm(vmin=1e-3, vmax=2e6))
plt.colorbar()
plt.subplot(132)
plt.imshow(hdu_OD3.data[700:1350, 700:1350], origin='lower', norm=LogNorm(vmin=1e-3, vmax=2e6))
plt.colorbar()
plt.subplot(133)
plt.imshow(hdu_OD4.data[700:1350, 700:1350], origin='lower', norm=LogNorm(vmin=1e-3, vmax=2e6))
plt.colorbar();
```

```{code-cell} ipython3
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, sharey=True, figsize=(15, 4))

ax1.plot(hdu_open.data[800:1250, 1024])
ax1.set_title("ND filter: open")
ax2.plot(hdu_OD3.data[800:1250, 1024])
ax2.set_title("ND filter: 1e-3")
ax3.plot(hdu_OD4.data[800:1250, 1024])
ax3.set_title("ND filter: 1e-4");
```

## Adding a custom filter to the filter wheel
A custom filter that is not in the default filter set can be added to the wheel using the method `add_filter`. A "filter" is an object of class `TERCurve` (or one of its subclasses) and the various methods for instantiating such an object can be used.

```{code-cell} ipython3
newfilter = sim.effects.ter_curves.TopHatFilterCurve(
    transmission=0.9,
    blue_cutoff=3.8,
    red_cutoff=3.9,
    name="custom_tophat",
)
metis['filter_wheel'].add_filter(newfilter)
metis['filter_wheel'].filters
```

```{code-cell} ipython3
metis['filter_wheel'].change_filter("custom_tophat")
metis['filter_wheel'].current_filter.plot();
```
