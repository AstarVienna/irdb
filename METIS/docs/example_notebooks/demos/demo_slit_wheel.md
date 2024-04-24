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

# How to use the slit wheel for spectroscopy (and imaging)

This notebook demonstrates how to use the various slits in METIS. They are defined in a `SlitWheel` effect, which works in the same way as `FilterWheel`. The notebook uses imaging mode to show the slits directly.

```{code-cell} ipython3
from matplotlib import pyplot as plt

import scopesim as sim

# Edit this path if you have a custom install directory, otherwise comment it out.
# sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../../"
```

If you haven't got the instrument packages yet, uncomment the following cell.

```{code-cell} ipython3
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=['img_lm'])
```

In imaging mode, `"!OBS.slit"` is `false` by default, i.e. there is no slit in the path. However, slits can be used in imaging as well by setting `!OBS.slit` to one of the slits available in the METIS package.

```{code-cell} ipython3
cmd['!OBS.slit'] = "C-38_1"

src = sim.source.source_templates.empty_sky()
metis = sim.OpticalTrain(cmd)
```

The following slits are now available and can be selected with `metis['slit_wheel'].change_slit()` as demonstrated below.

```{code-cell} ipython3
for slit in metis['slit_wheel'].slits:
    print(slit)
```

```{code-cell} ipython3
implanes = {}
for slit in metis['slit_wheel'].slits:
    metis['slit_wheel'].change_slit(slit)
    metis.observe(src, update=True)
    implanes[slit] = metis.image_planes[0].data
```

```{code-cell} ipython3
plt.figure(figsize=(15, 5))
for i, slit in enumerate(metis['slit_wheel'].slits):
    plt.subplot(2, 3, i+1)
    plt.imshow(implanes[slit][600:1450,], origin='lower')
    plt.title("Slit " + slit)
```

## Adding a slit to the slit wheel

The slit wheel holds a number of default slits (defined by the configuration for the instrument used). A custom slit can be added using the method `add_slit`. A "slit" is an object of class `ApertureMask` and the various methods for instantiating such an object can be used.

```{code-cell} ipython3
newslit = sim.effects.ApertureMask(
    name="Square",
    array_dict={
        "x": [-1, 1, 1, -1],
        "y": [-1, -1, 1, 1],
    },
    x_unit="arcsec",
    y_unit="arcsec",
)
metis['slit_wheel'].add_slit(newslit)
for slit in metis['slit_wheel'].slits:
    print(slit)
```

```{code-cell} ipython3
:tags: [hide-output]

metis['slit_wheel'].change_slit("Square")
metis.observe(src, update=True)
```

```{code-cell} ipython3
implane = metis.image_planes[0].data
plt.imshow(implane[600:1450,], origin='lower')
plt.title("Slit " + metis['slit_wheel'].current_slit.meta['name']);
```
