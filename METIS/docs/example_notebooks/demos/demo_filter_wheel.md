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
for filt in metis['filter_wheel'].filters:
    print(filt)
```

At any moment one of these filters is in the optical path and used for the simulation. Initially, this is the one set by `!OBS.filter_name`:

```{code-cell} ipython3
print(metis['filter_wheel'].current_filter)
```

The current filter can be changed to any of the filters in the list:

```{code-cell} ipython3
metis['filter_wheel'].change_filter("PAH_3.3")
print(metis['filter_wheel'].current_filter)
```

## Observing the same source in different filters

```{code-cell} ipython3
:tags: [hide-output]

src = sim.source.source_templates.empty_sky()

metis['filter_wheel'].change_filter("Lp")

metis.observe(src)
img_Lp = metis.image_planes[0].data

metis['filter_wheel'].change_filter("PAH_3.3")

metis.observe(src, update=True)
```

```{code-cell} ipython3
img_PAH = metis.image_planes[0].data

print(f"Background in Lp:      {np.median(img_Lp):8.1f} counts/s")
print(f"Background in PAH_3.3: {np.median(img_PAH):8.1f} counts/s")
```

## Using the neutral-density filter wheel

METIS also has neutral-density filters that can be inserted and changed using the `nd_filter_wheel` effect. The transmission of the filter `ND_ODx` is $10^{-x}$.

```{code-cell} ipython3
for filt in metis['nd_filter_wheel'].filters:
    print(filt)
```

```{code-cell} ipython3
print(metis['nd_filter_wheel'].current_filter)
```

Observe a bright star (default arguments result in Vega at 0 mag) in the Lp filter. It will be found that the star saturates the detector in the open position, and requires the `ND_OD4` filter not to do so.

```{code-cell} ipython3
star = sim.source.source_templates.star()

metis['filter_wheel'].change_filter('Lp')
```

```{code-cell} ipython3
:tags: [hide-output]

metis['nd_filter_wheel'].change_filter("open")
metis.observe(star, update=True)
```

```{code-cell} ipython3
hdu_open = metis.readout(dit=None, ndit=None)[0][1]
```

```{code-cell} ipython3
:tags: [hide-output]

metis['nd_filter_wheel'].change_filter("ND_OD3")
metis.observe(star, update=True)
```

```{code-cell} ipython3
hdu_OD3 = metis.readout(dit=None, ndit=None)[0][1]
```

```{code-cell} ipython3
:tags: [hide-output]

metis['nd_filter_wheel'].change_filter("ND_OD4")
metis.observe(star, update=True)
```

```{code-cell} ipython3
hdu_OD4 = metis.readout(dit=None, ndit=None)[0][1]
```

```{code-cell} ipython3
vmin, vmax = 1e2, 1e6
imgslice = slice(700, 1350), slice(700, 1350)
pltslice = slice(850, 1200), 1024
fig, axes = plt.subplots(2, 3, sharey="row", figsize=(12, 6),
                         gridspec_kw={"height_ratios": [3, 2]},
                         layout="constrained")
cmap = axes[0, 0].imshow(
    hdu_open.data[imgslice].clip(min=0),
    origin="lower", norm=LogNorm(vmin=vmin, vmax=vmax))
fig.colorbar(cmap)
axes[0, 0].set_title("ND filter: open")
axes[1, 0].plot(hdu_open.data[pltslice])

cmap = axes[0, 1].imshow(
    hdu_OD3.data[imgslice].clip(min=0),
    origin="lower", norm=LogNorm(vmin=vmin, vmax=vmax))
fig.colorbar(cmap)
axes[0, 1].set_title("ND filter: 1e-3")
axes[1, 1].plot(hdu_OD3.data[pltslice])

cmap = axes[0, 2].imshow(
    hdu_OD4.data[imgslice].clip(min=0),
    origin="lower", norm=LogNorm(vmin=vmin, vmax=vmax))
fig.colorbar(cmap)
axes[0, 2].set_title("ND filter: 1e-4")
axes[1, 2].plot(hdu_OD4.data[pltslice]);
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
for filt in metis['filter_wheel'].filters:
    print(filt)
```

```{code-cell} ipython3
metis['filter_wheel'].change_filter("custom_tophat")
metis['filter_wheel'].current_filter.plot();
```

```{code-cell} ipython3

```
