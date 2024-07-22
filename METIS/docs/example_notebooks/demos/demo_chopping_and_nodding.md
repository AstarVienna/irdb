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

# How to produce chop-nod difference images in the N band

This notebook demonstrates how to use the `ChopNod` effect in Scopesim. Both chopping and nodding are currently defined as two-point patterns, where the throw direction is given as a 2D vector (dx, dy) in `metis['chop_nod'].meta['chop_offsets']` and `metis['chop_nod'].meta['nod_offsets']`. For parallel nodding, the two vectors are parallel (typically nod_offset = - chop_offset, giving a three-point pattern), for perpendicular nodding, the vectors are orthogonal.

```{code-cell} ipython3
from matplotlib import pyplot as plt

import scopesim as sim

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../../" 
```

If you haven't got the instrument packages yet, uncomment the following cell.

```{code-cell} ipython3
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=['img_n'])

metis = sim.OpticalTrain(cmd)
metis['chop_nod'].include = True
```

The default is perpendicular nodding, with the chop throw in the x-direction and the nod throw in the y direction.

```{code-cell} ipython3
print(f"Chop offsets: {metis.cmds[metis['chop_nod'].meta['chop_offsets']]}")
print(f"Nod offsets:  {metis.cmds[metis['chop_nod'].meta['nod_offsets']]}")
```

```{code-cell} ipython3
:tags: [hide-output]

src = sim.source.source_templates.star(flux=15)

metis.observe(src, update=True)
```

```{code-cell} ipython3
imghdu = metis.readout(exptime=1000000, dit=None, ndit=None)[0][1]
```

```{code-cell} ipython3
plt.imshow(imghdu.data, origin='lower', vmin=-5e7, vmax=5e7)
plt.colorbar()
```

For parallel nodding, turn the nod throw into the x-direction as well.

```{code-cell} ipython3
metis['chop_nod'].meta['nod_offsets'] = [-3, 0]
```

```{code-cell} ipython3
imghdu_par = metis.readout(exptime=1000000, dit=None, ndit=None)[0][1]
```

```{code-cell} ipython3
plt.imshow(imghdu_par.data, origin='lower', vmin=-5e7, vmax=5e7)
```

Other four-point patterns are possible:

```{code-cell} ipython3
metis['chop_nod'].meta['nod_offsets'] = [-3, 3]
imghdu_3 = metis.readout(exptime=1000000, dit=None, ndit=None)[0][1]
plt.imshow(imghdu_3.data, origin='lower', vmin=-5e7, vmax=5e7)
```

```{code-cell} ipython3
metis['chop_nod'].meta['chop_offsets'] = [-3, 2]
metis['chop_nod'].meta['nod_offsets'] = [2, 3]
imghdu_4 = metis.readout(exptime=1000000, dit=None, ndit=None)[0][1]
plt.imshow(imghdu_4.data, origin='lower', vmin=-5e7, vmax=5e7)
```

```{code-cell} ipython3

```
