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

# Basic procedure for long-slit spectroscopy

This notebook shows the most basic setup for long-slit spectroscopy, using a star as the source.

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

Set up the instrument in lss_l mode:

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=['lss_l'])
metis = sim.OpticalTrain(cmd)
```

The source is a star with Vega spectrum and apparent brightness of 12 mag.

```{code-cell} ipython3
:tags: [hide-output]
src = sim.source.source_templates.star(flux=12)

metis.observe(src, update=True)
```

```{code-cell} ipython3
result = metis.readout(detector_readout_mode="auto")[0][1]

plt.figure(figsize=(12,10))
plt.imshow(result.data, origin='lower', norm=LogNorm(vmin=100))
plt.colorbar();
```

## Realistic spectral mapping

The default configuration for METIS applies a mapping of the two-dimensional spectrum onto the detector that is perfectly linear in both the wavelength and spatial directions. The trace definitions for the actual expected mappings are also available. To use them, the parameter `!OBS.trace_file` needs to be set. The difference is fairly small.

```{code-cell} ipython3
:tags: [hide-output]
cmds = sim.UserCommands(use_instrument="METIS", set_modes=['lss_l'])
cmds['!OBS.trace_file'] = "TRACE_LSS_L.fits"

metis = sim.OpticalTrain(cmds)

metis.observe(src, update=True)
```

```{code-cell} ipython3
result_2 = metis.readout()[0][1]

plt.figure(figsize=(12,10))
plt.imshow(result_2.data, origin='lower', norm=LogNorm(vmin=100))
plt.colorbar();
```
