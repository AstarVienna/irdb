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

# Auto Exposure

This is a setup/test/demonstration notebook for the `AutoExposure` effect in Scopesim. This effect splits the requested total exposure time into NDIT subexposures of integration time DIT such that the maximum counts in a single subexposure does not exceed a certain fill fraction of the detector full well. The final readout is the sum over the NDIT subexposures, i.e. corresponds to the total requested exposure time.

The notebook uses the `irdb/METIS` configuration. The observed source is blank sky, except for the last example where a star of 0 mag is used (Vega).

```{code-cell} ipython3
from astropy import units as u
import scopesim as sim
sim.bug_report()

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.link_irdb("../../../../")
```

If you haven't got the instrument packages yet, uncomment the following cell. 

```{code-cell} ipython3
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

## Imaging LM-band

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
metis = sim.OpticalTrain(cmd)
```

```{code-cell} ipython3
metis.observe()
```

For `AutoExposure` to work the exposure time has to be given explicitely as a parameter to the `readout` method. If this is not done, the default values for `DIT` and `NDIT` will be used. The following is for an exposure time of 1 second. The resulting readout is divided by `NDIT` to produce the average over the `NDIT` subexposures. After application of the gain to convert from ADU to electrons this allows direct comparison to the detector full well. 

```{code-cell} ipython3
outhdul = metis.readout(exptime=1)[0]
gain = outhdul[1].header["ESO DET1 CHIP GAIN"] * u.electron / u.adu
full_well = outhdul[1].header["ESO DET1 CHIP FULLWELL"] * u.electron
outimg = outhdul[1].data * u.adu * gain
fill_frac = outimg.max() / full_well << u.percent

print("\nResult\n======")
print(f"Maximum value in readout: {outimg.max():7.1f} (per DIT)")
print(f"Detector full well: {full_well:13.0f}")
print(f"Fill fraction: {fill_frac:18.1f}")
```

The same with a much larger exposure time of 1000 seconds:

```{code-cell} ipython3
outhdul = metis.readout(exptime = 1000)[0]
gain = outhdul[1].header["ESO DET1 CHIP GAIN"] * u.electron / u.adu
full_well = outhdul[1].header["ESO DET1 CHIP FULLWELL"] * u.electron
outimg = outhdul[1].data * u.adu * gain
fill_frac = outimg.max() / full_well << u.percent

print("\nResult\n======")
print(f"Maximum value in readout: {outimg.max():7.1f} (per DIT)")
print(f"Detector full well: {full_well:13.0f}")
print(f"Fill fraction: {fill_frac:18.1f}")
```

The desired fill fraction can be changed with the argument `fill_frac`. The default value of 75 per cent is a typical good value that keeps the detector counts within the linear regime.

```{code-cell} ipython3
outhdul = metis.readout(exptime = 1000, fill_frac=0.9)[0]
gain = outhdul[1].header["ESO DET1 CHIP GAIN"] * u.electron / u.adu
full_well = outhdul[1].header["ESO DET1 CHIP FULLWELL"] * u.electron
outimg = outhdul[1].data * u.adu * gain
fill_frac = outimg.max() / full_well << u.percent

print("\nResult\n======")
print(f"Maximum value in readout: {outimg.max():7.1f} (per DIT)")
print(f"Detector full well: {full_well:13.0f}")
print(f"Fill fraction: {fill_frac:18.1f}")
```

## Imaging N-band

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_n"])
metis = sim.OpticalTrain(cmd)
```

```{code-cell} ipython3
metis.observe()
```

```{code-cell} ipython3
outhdul = metis.readout(exptime=1)[0]
gain = outhdul[1].header["ESO DET2 CHIP GAIN"] * u.electron / u.adu
full_well = outhdul[1].header["ESO DET2 CHIP FULLWELL"] * u.electron
outimg = outhdul[1].data * u.adu * gain
fill_frac = outimg.max() / full_well << u.percent

print("\nResult\n======")
print(f"Maximum value in readout: {outimg.max():7.1f} (per DIT)")
print(f"Detector full well: {full_well:13.0f}")
print(f"Fill fraction: {fill_frac:18.1f}")
```

## Long-slit spectroscopy

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["lss_l"],
                       properties={"!OBS.interp_psf": False})
metis = sim.OpticalTrain(cmd)
```

```{code-cell} ipython3
metis.observe()
```

```{code-cell} ipython3
outhdul = metis.readout(exptime=3600.)[0]
gain = outhdul[1].header["ESO DET1 CHIP GAIN"] * u.electron / u.adu
full_well = outhdul[1].header["ESO DET1 CHIP FULLWELL"] * u.electron
outimg = outhdul[1].data * u.adu * gain
fill_frac = outimg.max() / full_well << u.percent

print("\nResult\n======")
print(f"Maximum value in readout: {outimg.max():7.1f} (per DIT)")
print(f"Detector full well: {full_well:13.0f}")
print(f"Fill fraction: {fill_frac:18.1f}")
```

## What happens when the source saturates the detector?
We take an N-band image of Vega. `DIT` is automatically set to the minimum value supported by the detector, but the centre of the star still saturates the detector. In the final image, the star's profile is capped at the full well of the detector.

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_n"])
metis = sim.OpticalTrain(cmd)
```

```{code-cell} ipython3
src = sim.source.source_templates.star()
```

```{code-cell} ipython3
metis.observe(src)
```

```{code-cell} ipython3
outhdul = metis.readout(exptime=1)[0]
gain = outhdul[1].header["ESO DET2 CHIP GAIN"] * u.electron / u.adu
full_well = outhdul[1].header["ESO DET2 CHIP FULLWELL"] * u.electron
outimg = outhdul[1].data * u.adu * gain
fill_frac = outimg.max() / full_well << u.percent

print("\nResult\n======")
print(f"Maximum value in readout: {outimg.max():7.1f} (per DIT)")
print(f"Detector full well: {full_well:13.0f}")
print(f"Fill fraction: {fill_frac:18.1f}")
```

Plot a cut through the star to show how its peak saturates the detector.

```{code-cell} ipython3
from matplotlib import pyplot as plt
%matplotlib inline
```

```{code-cell} ipython3
plt.plot(outimg[950:1100, 1024])
```

```{code-cell} ipython3
npix = (outimg >= full_well).sum()
print("Number of saturated pixels:", npix)
```

The default values for the detector full well in the various modes reflects our current best knowledge of the properties of the actual METIS detectors. These values can be changed as in the following example, but be aware that this makes the simulations unrealistic.

+++

**NB: There's something wrong with this example, please ignore for the time being.**

```{code-cell} ipython3
full_well = 1000 * metis.cmds["!DET.full_well"] * u.electron
outhdul = metis.readout(exptime=1, full_well=full_well)[0]
gain = outhdul[1].header["ESO DET2 CHIP GAIN"] * u.electron / u.adu
outimg = outhdul[1].data * u.adu * gain
fill_frac = outimg.max() / full_well << u.percent

print("\nResult\n======")
print(f"Maximum value in readout: {outimg.max():7.1f} (per DIT)")
print(f"Detector full well: {full_well:13.0f}")
print(f"Fill fraction: {fill_frac:18.1f}")
```
