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

# How to select `dit`/`ndit` automatically

This is a setup/test/demonstration notebook for the `AutoExposure` effect in Scopesim. The notebook uses the `irdb/METIS` configuration. The observed source is blank sky, except for the last example where a star of 0 mag is used (Vega).

```{code-cell} ipython3
import scopesim as sim
sim.bug_report()

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../../"
```

If you haven't got the instrument packages yet, uncomment the following cell. 

```{code-cell} ipython3
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

## Imaging LM-band

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
metis = sim.OpticalTrain(cmd)
src = sim.source.source_templates.empty_sky()
metis.observe(src)
```

```{code-cell} ipython3
outimg = metis.readout()[0][1].data 
outimg /= metis.cmds[metis['summed_exposure'].meta['ndit']]

full_well = metis.cmds["!DET.full_well"]
print("\nResult\n======")
print(f"Maximum value in readout (per DIT): {outimg.max():8.1f}")
print(f"Detector full well:                 {full_well:8.1f}")
print(f"Fill fraction:                      {outimg.max() / full_well:8.1%}")
```

Exposure time can be changed with an argument to `metis.readout()`:

```{code-cell} ipython3
outimg = metis.readout(exptime = 1000)[0][1].data 
outimg /= metis.cmds[metis['summed_exposure'].meta['ndit']]

full_well = metis.cmds["!DET.full_well"]
print("\nResult\n======")
print(f"Maximum value in readout (per DIT): {outimg.max():8.1f}")
print(f"Detector full well:                 {full_well:8.1f}")
print(f"Fill fraction:                      {outimg.max() / full_well:8.1%}")
```

## Imaging N-band

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=['img_n'])
metis = sim.OpticalTrain(cmd)
metis.observe(src)
```

```{code-cell} ipython3
outimg = metis.readout()[0][1].data 
outimg /= metis.cmds[metis['summed_exposure'].meta['ndit']]

full_well = metis.cmds["!DET.full_well"]
print("\nResult\n======")
print(f"Maximum value in readout (per DIT): {outimg.max():9.1f}")
print(f"Detector full well:                 {full_well:9.1f}")
print(f"Fill fraction:                      {outimg.max() / full_well:9.1%}")
```

## Long-slit spectroscopy

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=['lss_l'])
metis = sim.OpticalTrain(cmd)
metis.observe(src)
```

```{code-cell} ipython3
outimg = metis.readout(exptime=3600.)[0][1].data 
outimg /= metis.cmds[metis['summed_exposure'].meta['ndit']]

full_well = metis.cmds["!DET.full_well"]

print("\nResult\n======")
print(f"Maximum value in readout (per DIT): {outimg.max():8.1f}")
print(f"Detector full well:                 {full_well:8.1f}")
print(f"Fill fraction:                      {outimg.max() / full_well:8.1%}")
```

## What happens when the source saturates the detector?

Use N-band imaging of Vega. DIT is automatically set to the minimum possible value, but the centre of the star still saturates the detector. In the final image, the star's profile is capped at the full well of the detector.

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_n"])
metis = sim.OpticalTrain(cmd)
src = sim.source.source_templates.star()
metis.observe(src)
```

```{code-cell} ipython3
outimg = metis.readout()[0][1].data
outimg /= metis.cmds[metis['summed_exposure'].meta['ndit']]

full_well = metis.cmds["!DET.full_well"]

print("\nResult\n======")
print(f"Maximum value in readout (per DIT): {outimg.max():9.1f}")
print(f"Detector full well:                 {full_well:9.1f}")
print(f"Fill fraction:                      {outimg.max() / full_well:9.1%}")
```

Plot a cut through the star to show how its peak saturates the detector.

```{code-cell} ipython3
from matplotlib import pyplot as plt

plt.plot(outimg[950:1100, 1024])
```

```{code-cell} ipython3
print(f"Number of saturated pixels: {(outimg >= full_well).sum():d}")
```
