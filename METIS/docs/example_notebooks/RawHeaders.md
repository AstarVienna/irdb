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

# How to show the raw headers of the simulated data

A notebook to show the raw headers of the simulated data.

```{code-cell} ipython3
:tags: [hide-output]
import os
import numpy as np

from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

from astropy.io import fits
from astropy import units as u
from astropy.wcs import WCS

import scopesim as sim
import scopesim_templates
# Edit this path to use where you have downloaded the IRDB packages (see other notebooks).
sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../"
```

```{code-cell} ipython3
star = scopesim_templates.stellar.star(filter_name="V", amplitude=22)

cmd_img_lm = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
metis_img_lm = sim.OpticalTrain(cmd_img_lm)
metis_img_lm.observe(star)
hdus_img_lm = metis_img_lm.readout()[0]
```

```{code-cell} ipython3
header_primary_img_lm = hdus_img_lm[0].header

print(repr(header_primary_img_lm))
```

```{code-cell} ipython3
header_data_img_lm = hdus_img_lm[1].header

print(repr(header_data_img_lm))
```
