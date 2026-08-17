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

# Selecting detector modes in METIS
This notebook demonstrates the effect `detector_readout_parameters`, which selects between the different detector readout modes. These are `fast` and `slow` for the HAWAII2RG detectors, and `high_capacity` and `low_capacity` for the Geosnap detector.

```{code-cell} ipython3
import numpy as np
from astropy import units as u
from matplotlib import pyplot as plt

import scopesim as sim
sim.bug_report()

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.link_irdb("../../../../")
```

If you haven't got the instrument packages yet, uncomment the following cell.

```{code-cell} ipython3
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
```

The default readout mode for `img_lm` is the fast mode:

```{code-cell} ipython3
cmd["!OBS.detector_readout_mode"]
```

We build the optical train using the default mode, and then check that the relevant parameters (`mindit`, `full_well`, `readout_noise` and `dark_current`) are taken over correctly, first in the `cmds` property of the optical train, then - most importantly - into the parameters of the affected `Effect` objects (demonstrated for the `readout_noise` effect).

```{code-cell} ipython3
metis = sim.OpticalTrain(cmd)
```

```{code-cell} ipython3
metis.cmds["!DET"]
```

```{code-cell} ipython3
metis['readout_noise'].meta['noise_std']
```

The "bang string" here means that the value is taken from the `cmds` structure in the previous cell, i.e.

```{code-cell} ipython3
metis.cmds[metis['readout_noise'].meta['noise_std']]
```

At this stage, we have access to the available detector modes and the parameter values that are set by them:

```{code-cell} ipython3
print(metis['detector_readout_parameters'].list_modes())
```

We can switch to the `slow` mode in the existing optical train by doing

```{code-cell} ipython3
metis.cmds["!OBS.detector_readout_mode"] = "slow"
metis.update()
```

```{code-cell} ipython3
metis.cmds["!DET"]
```

```{code-cell} ipython3
metis.cmds[metis['readout_noise'].meta['noise_std']]
```

## Test: detector noise level (LSS-L)
To investigate the behaviour of the detector readout modes, we look at the L-band long-slit mode where the areas of the detector outside the spectral trace contain only readout noise and dark current. The default mode for long-slit spectroscopy is the `slow` mode, and we'll switch to the `fast` mode afterwards.

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["lss_l"])
metis = sim.OpticalTrain(cmd)
```

```{code-cell} ipython3
print("Detector mode:", metis.cmds["!OBS.detector_readout_mode"])
metis['psf'].include = False     # not needed for blank-sky observations
metis.observe()
hdul_slow = metis.readout(exptime=1000)[0]
```

We get the statistics in a strip at the left edge of the detector that is not covered by any source or background flux and compare to the expected values.

```{code-cell} ipython3
ndit_slow = metis.cmds["!OBS.ndit"]
dit_slow = metis.cmds["!OBS.dit"]

bg_slow = hdul_slow[1].data[250:1750, 10:200].mean()
bg_slow_expected = dit_slow * ndit_slow * metis.cmds["!DET.dark_current"]

noise_slow = hdul_slow[1].data[250:1750, 10:200].std()
noise_slow_expected = np.sqrt(ndit_slow) * metis.cmds["!DET.readout_noise"]
```

Do the same for the `fast` mode.

```{code-cell} ipython3
hdul_fast = metis.readout(detector_readout_mode="fast", exptime=1000)[0]
```

```{code-cell} ipython3
ndit_fast = metis.cmds["!OBS.ndit"]
dit_fast = metis.cmds["!OBS.dit"]

bg_fast = hdul_fast[1].data[250:1750, 10:200].mean()
bg_fast_expected = dit_fast * ndit_fast * metis.cmds["!DET.dark_current"]

noise_fast = hdul_fast[1].data[250:1750, 10:200].std()
noise_fast_expected = np.sqrt(ndit_fast) * metis.cmds["!DET.readout_noise"]
```

```{code-cell} ipython3
print(f"""
Fast: ndit  = {ndit_fast}     dit = {dit_fast:.2f}
      bg    = {bg_fast:5.1f}   expected: {bg_fast_expected:5.1f}
      noise = {noise_fast:5.1f}  expected: {noise_fast_expected:5.1f}""")
print(f"""
Slow: ndit  = {ndit_slow}     dit = {dit_slow:.2f}
      bg    = {bg_slow:5.1f}   expected: {bg_slow_expected:5.1f}
      noise = {noise_slow:5.1f}   expected: {noise_slow_expected:.1f}""")
```

Finally, we can let Scopesim automatically select the "best" mode.

```{code-cell} ipython3
hdul_auto = metis.readout(detector_readout_mode="auto", exptime=1000)[0]
```

The advantage of the "slow" mode of the H2RG detector is the low readout noise. The "fast" mode permit smaller DITs and would be selected for bright sources that would saturate the detector at the minimum DIT of the "slow" mode.

## Test: Full well (IMG-N)
This demonstrates the high- and low-capacity modes of the Geosnap detector. The setup uses a neutral-density filter to ensure that the background does not saturate the detector in the low-capacity mode. The source is a very bright star, which saturates in the low-capacity mode but does not in the high-capacity mode.

```{code-cell} ipython3
star = sim.source.source_templates.star(flux=20 * u.Jy)

cmd_n = sim.UserCommands(use_instrument="METIS", set_modes=['img_n'],
                        properties={"!OBS.filter_name": "N2", "!OBS.nd_filter_name": "ND_OD1"})
metis_n = sim.OpticalTrain(cmd_n)
```

```{code-cell} ipython3
metis_n.observe(star, update=True)
print("--- high-capacity mode ---")
hdul_high = metis_n.readout(detector_readout_mode="high_capacity", exptime=1)[0]
fullwell_high = metis_n.cmds["!DET.full_well"]
gain_high = metis_n.cmds["!DET.gain"]
ndit_high = metis_n.cmds["!OBS.ndit"]

print("--- low-capacity mode ---")
hdul_low = metis_n.readout(detector_readout_mode="low_capacity", exptime=1)[0]
fullwell_low = metis_n.cmds["!DET.full_well"]
gain_low = metis_n.cmds["!DET.gain"]
ndit_low = metis_n.cmds["!OBS.ndit"]
```

We take the average over NDIT exposures (units: electrons per DIT) so that we can immediately compare the counts to the full wells for the two modes.

```{code-cell} ipython3
detimg_high = hdul_high[1].data * gain_high
detimg_low = hdul_low[1].data * gain_low
```

```{code-cell} ipython3
plt.figure(figsize=(12, 4))
plt.subplot(121)
plt.plot(detimg_high[1024, 974:1074])
plt.title("high-capacity mode")
plt.hlines(fullwell_high, 0, 100, colors='k', linestyles='dashed')
plt.ylabel("Electrons per DIT")

plt.subplot(122)
plt.plot(detimg_low[1024, 974:1074])
plt.title(label="low-capacity mode")
plt.hlines(fullwell_low, 0, 100, colors='k', linestyles="dashed")
plt.ylabel("Electrons per DIT");
```
