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

# Inter-Pixel Capacitance
This notebook demonstrates the ScopeSim effect `InterPixelCapacitance`. Inter-pixel capacitance correlates the voltages or data values measured in adjacent pixels of an infrared detector. The effect implements the three-parameter model of Kannawadi et al. (2016) (PASP 128, 095001) and applies the following convolution kernel (in their notation) to the detector readout:
$$ K(\alpha, \alpha^\prime, \alpha_{+}) = \begin{pmatrix}
   \alpha^\prime & \alpha - \alpha_{+} & \alpha^\prime \\
   \alpha + \alpha_{+} & 1 - 4(\alpha + \alpha^\prime) & \alpha + \alpha_{+} \\
   \alpha^\prime & \alpha - \alpha_{+} & \alpha^\prime
   \end{pmatrix}
$$

The correspondence between these parameters and those of the Scopesim effect is as follows:
- $\alpha$ -- ``alpha_edge``: gives the influence of the four pixels sharing an edge with the target pixel.
- $\alpha^\prime$ -- ``alpha_corner``: gives the influence of the four pixels sharing a corner with the target pixel.
- $\alpha_{+}$ -- ``alpha_aniso``: gives a difference in the influence of neighbouring pixels along rows and along columns

The default setting in the instrument package sets these parameter with literature values typical for HxRG detectors.
It is also possible to set the kernel directly in the yaml file. This allows using kernels that are larger than $3\times 3$.

When the $\alpha$ parameters are used to define the IPC kernel it is automatically normalised to unit sum. When the kernel is provided it is normalised by ScopeSim when its sum is greater than one. When it is less than one (but larger than zero), it is accepted as is, which then leads to loss of flux -- it is the user's responsibility to ensure the kernel is normalised unless this flux loss is intended. Kernels with negative sum are rejected and raise a `ValueError`.

```{code-cell} ipython3
import numpy as np
from matplotlib import pyplot as plt
from astropy import units as u
```

```{code-cell} ipython3
import scopesim as sim
sim.bug_report()

# Edit this path if you have a custom install directory, otherwise comment it out. [For ReadTheDocs only]
sim.link_irdb("../../../../")
```

If you haven't got the instrument packages yet, uncomment the following cell, which will install the packages into `./inst_pkgs`, a subdirectory of your current working directory. If you have already downloaded the packages but to a different location you can set
```python
sim.set_inst_pgks_path("/path/to/inst/pkgs")
```

```{code-cell} ipython3
# sim.download_package(["METIS", "ELT", "Armazones"])
```

The `InterPixelCapacitance` effect will be demonstrated in the METIS IMG_LM mode. It will become active in the `readout()` step.

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])
```

```{code-cell} ipython3
metis = sim.OpticalTrain(cmd)
```

```{code-cell} ipython3
metis.effects.pprint_all()
```

```{code-cell} ipython3

```

```{code-cell} ipython3
print(metis['ipc'])
```

The kernel can be replaced using the `update` method. Note that the parameters need to be specified in full, either as `kernel` or the three `alpha` parameters (`alpha` parameters that are not set explicitly default to zero):

```{code-cell} ipython3
metis['ipc'].update(alpha_edge=0.02, alpha_corner=0.002, alpha_aniso=0.001)
print(metis['ipc'])
```

## Effect on noise
The IPC effect is applied after dark current and shot noise but before readout noise. Its main effect is to correlate the photon noise, which is for instance measurable as a decrease in the rms noise. To show this, we observe a piece of blank sky and read out with and without the IPC effect included.

```{code-cell} ipython3
metis.observe()
```

```{code-cell} ipython3
metis['ipc'].include = True         # this is the default
with_ipc = metis.readout(exptime=10)[0]
```

```{code-cell} ipython3
metis['ipc'].include = False
without_ipc = metis.readout(exptime=10)[0]
```

```{code-cell} ipython3
# The edge rows and columns need to be discarded as they are incompletely covered by the IPC kernel
print(f"RMS noise without IPC: {without_ipc[1].data[1:-1, 1:-1].std()}")
print(f"RMS noise with IPC:    {with_ipc[1].data[1:-1, 1:-1].std()}")
```

## Effect on image quality
The effect on the image quality is rather slight, in particular because the SCAO PSF in the L band is broad with a FWHM of about five pixels. We simulate a star and apply the default SCAO PSF.

```{code-cell} ipython3
star = sim.source.source_templates.star(flux=0.01*u.Jy)
```

```{code-cell} ipython3
metis.observe(star)
```

```{code-cell} ipython3
metis['ipc'].include = True
star_w_ipc = metis.readout(exptime=1)[0]
metis['ipc'].include = False
star_wo_ipc = metis.readout(exptime=1)[0]
```

```{code-cell} ipython3
plt.plot(np.arange(1010,1035), star_wo_ipc[1].data[1023, 1010:1035], label="without IPC")
plt.plot(np.arange(1010, 1035), star_w_ipc[1].data[1023, 1010:1035], label="with IPC")
plt.legend();
```

```{code-cell} ipython3
plt.plot(np.arange(1010, 1035), (star_w_ipc[1].data - star_wo_ipc[1].data)[1023, 1010:1035], label="Difference (with_ipc - without_ipc)")
plt.legend();
```

The effect is also more pronounced with a different (though unrealistic) kernel:

```{code-cell} ipython3
metis['ipc'].update(kernel=[[1, 1, 1], [1, 1, 1], [1, 1, 1]])
print(metis['ipc'])
```

```{code-cell} ipython3
metis['ipc'].include = True
star_w_strong_ipc = metis.readout(exptime=1)[0]
```

```{code-cell} ipython3
plt.plot(np.arange(1010,1035), star_wo_ipc[1].data[1023, 1010:1035], label="without IPC")
plt.plot(np.arange(1010, 1035), star_w_strong_ipc[1].data[1023, 1010:1035], label="with strong IPC")
plt.legend();
```
