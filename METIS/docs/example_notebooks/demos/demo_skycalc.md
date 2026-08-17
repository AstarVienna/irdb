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

# The `SkycalcTERCurve` effect in ScopeSim

This notebook demonstrates how to work with the skycalc effect, `SkycalcTERCurve`. This effect provides the atmospheric emission and transmission that are applied to a source object in ScopeSim. The effect is based on `skycalc_ipy`, a python wrapper to ESO’s SkyCalc tool.

```{code-cell} ipython3
import numpy as np
from matplotlib import pyplot as plt
from astropy import units as u
```

```{code-cell} ipython3
import scopesim as sim

# If you have not done so already, please download the relevant instrument packages by uncommenting the following line:
# sim.download_packages(["Armazones", "ELT", "METIS"])
```

We use the `SkycalcTERCurve` in the context of METIS/LMS, although sky mode of any other instrument would do as well. 

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["lms"])
cmd["!OBS.wavelen"] = 3.5
```

```{code-cell} ipython3
metis = sim.OpticalTrain(cmd)
```

The METIS optical train includes the `SkycalcTERCurve` effect under the name `skycalc_atmosphere`. We assign it to a variable for convenience.

```{code-cell} ipython3
sky = metis['skycalc_atmosphere']
```

## Inspecting and modifying sky parameters

The list of parameters that are sent to the ESO skycalc server when requesting a sky spectrum can be obtained by simply printing the effect object:

```{code-cell} ipython3
print(sky)
```

The emission and transmission spectra are returned as columns in `sky.skycalc_table` and can be plotted as follows:

```{code-cell} ipython3
tbl = sky.skycalc_table

# Extract columns and restrict to a smaller wavelength range
wavelength = tbl['wavelength'].to(u.um)
idx = (wavelength > 3.4*u.um) * (wavelength < 3.6*u.um)
transmission = tbl['transmission']
emission = tbl['emission']

_, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
axes[0].plot(wavelength[idx], transmission[idx])
axes[0].set_ylabel("Transmission")
axes[0].set_xlim(3.4, 3.6)
axes[1].plot(wavelength[idx], emission[idx])
axes[1].set_xlabel(f"Wavelength [{wavelength.unit}]")
axes[1].set_ylabel(f"Radiance [{emission.unit}]");
```

The effect has an `update()` method that can be used to change parameter values. The names of the available parameters can be obtained from the list printed above.

```{code-cell} ipython3
sky.update(airmass=3., pwv=20.)
```

```{code-cell} ipython3
tbl2 = sky.skycalc_table

# Extract columns and restrict to a smaller wavelength range
wavelength2 = tbl2['wavelength'].to(u.um)
idx2 = (wavelength2 > 3.4*u.um) * (wavelength2 < 3.6*u.um)
transmission2 = tbl2['transmission']
emission2 = tbl2['emission']

_, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
axes[0].plot(wavelength[idx], transmission[idx], lw=1)
axes[0].plot(wavelength2[idx2], transmission2[idx2], lw=1)
axes[0].set_ylabel("Transmission")
axes[0].set_xlim(3.4, 3.6)
axes[1].plot(wavelength[idx], emission[idx], lw=1)
axes[1].plot(wavelength2[idx2], emission2[idx2], lw=1)
axes[1].set_xlabel(f"Wavelength [{wavelength.unit}]")
axes[1].set_ylabel(f"Radiance [{emission.unit}]");
```

## Use in simulations
As an example of how the sky parameters affect observations we simulate METIS N-band images for a number of values of PWV (precipitable water vapour) and record the median background level in the (noiseless) `ImagePlane`.

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_n"])
metis = sim.OpticalTrain(cmd)
metis['detector_linearity'].include = False    # to avoid saturation
```

```{code-cell} ipython3
sky = metis['skycalc_atmosphere']
```

```{code-cell} ipython3
pwv_values = [0.5, 5, 10, 20]
bg_level = []
plt.figure()
lam = np.linspace(7, 12, 1001) * u.um
for pwv in pwv_values:
    sky.update(pwv=pwv)
    plt.plot(sky.surface.table['wavelength'].to(u.um), sky.surface.table['emission'], label=f"pwv = {pwv}", alpha=0.7) 
    metis.observe()
    bg_level.append(np.median(metis.image_planes[0].data))
plt.legend();
```

```{code-cell} ipython3
plt.plot(pwv_values, bg_level, '-o')
plt.ylim(0, 3e8)
plt.xlabel("PWV [mm]")
plt.ylabel("ImagePlane level [e/s]");
```
