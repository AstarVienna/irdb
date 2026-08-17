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

The METIS detectors have a number of masked rows and pixels around their borders. These pixels do not see any signal but do have dark current, readout noise and other detector effects. This notebook shows what the effect `ReferencePixelBorder` does and how it is set up for METIS. It also explains how the dimensions of the mask can be changed and of course how the mask can be switched off entirely.

```{code-cell} ipython3
from matplotlib import pyplot as plt
```

```{code-cell} ipython3
import scopesim as sim
```

```{code-cell} ipython3
# Edit this path if you have a custom install directorym otherwise comment it out
sim.link_irdb("../../../../")

# If you haven't got the instrument packages yet, uncomment the following line
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

## Imager detectors

+++

The Imager detectors (H2RG for IMG-LM, Geosnap for IMG-N) have equal width masks all around, with 64 pixels for the H2RG and 28 pixels for the Geosnap. We look at the H2RG here and simulate a WCU flat field for simplicity.

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["wcu_img_lm"])
metis = sim.OpticalTrain(cmd)
metis.observe()
readout = metis.readout(ndit=1, dit=1.)[0]
```

```{code-cell} ipython3
_, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.imshow(readout[1].data)
ax1.set_title("IMG-LM flat field")
ax2.plot(readout[1].data[250,])
ax2.set_title("Row 250");
```

The dimensions of the mask are recorded the header of the image extension of the readout (the order is **b**ottom, **l**eft, **t**op, **r**ight):

```{code-cell} ipython3
print(readout[1].header["HIERARCH ESO DET1 CHIP REFPIX"])               # keyword value itself
print(readout[1].header.comments["HIERARCH ESO DET1 CHIP REFPIX"])      # keyword comment
```

To demonstrate that the masked pixels indeed get dark current, we increase the latter to an appreciable value.

```{code-cell} ipython3
metis["dark_current"].meta["value"] = 10000.
readout = metis.readout(ndit=1, dit=1.)[0]
```

```{code-cell} ipython3
_, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.imshow(readout[1].data)
ax1.set_title("IMG-LM flat field")
ax2.plot(readout[1].data[250,])
ax2.set_ylim(0, 26000)
ax2.set_ylabel("ADU")
ax2.set_title("Row 250");
```

Note that with a gain of 4 e/ADU, the reference level of 2500 ADU corresponds to 10000 electrons, as expected.

+++

## LMS detector array

The LMS detector array consists of 4 H2RG detectors. In the y-direction all detectors have 32 reference rows at the bottom and top. In the x-direction (the dispersion direction) only the outsides are masked with 64 columns, while there are no reference pixels on the inside. (The simulation takes several minutes.)

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["wcu_lms"])
metis = sim.OpticalTrain(cmd)
metis['psf'].include = False    # saves some simulation time
metis.observe()
readout = metis.readout(ndit=1, dit=300)[0]
```

```{code-cell} ipython3
_, [[ax1, ax2], [ax3, ax4]] = plt.subplots(2, 2, layout="tight", sharex=True, sharey=True)
ax1.imshow(readout[1].data)
ax2.imshow(readout[2].data)
ax3.imshow(readout[3].data)
ax4.imshow(readout[4].data)
```

## Modifying the behaviour of `ReferencePixelBorder`
When setting up the instrument, the detector mask can be defined with the parameter `!DET.border`:

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["wcu_img_lm"])
cmd["!DET.border"] = [0, 40, 80, 120]   # bottom left top right
metis = sim.OpticalTrain(cmd)
metis.observe()
readout = metis.readout(dit=1., ndit=1)[0]
```

```{code-cell} ipython3
plt.imshow(readout[1].data, origin='lower')
```

When the `OpticalTrain` already exists and has `observe`d a scene, the mask can be modified by changing the effect parameter:

```{code-cell} ipython3
metis['reference_pixel_mask'].meta["border"] = [300, 300, 300, 300]
readout = metis.readout(dit=1, ndit=1)[0]
```

```{code-cell} ipython3
plt.imshow(readout[1].data, origin='lower')
```

As always, the mask can be switched off entirely by setting

```{code-cell} ipython3
metis['reference_pixel_mask'].include = False
```

```{code-cell} ipython3
readout = metis.readout(dit=1., ndit=1)[0]
plt.imshow(readout[1].data, origin='lower')
```
