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

# WCU (AIT)
This notebook is targeted at the AIT team who use Scopesim to simulate observations with the warm calibration unit (WCU). It demonstrates how to select point-spread functions that correspond to a pupil-mask that is inserted in the optical path. This is an interplay between two effects in ScopeSim, an instance of `PupilMaskWheel` and an instance of `FieldConstantPSF`. Note that the instrument configuration for ScopeSim currently has a single pupil-mask wheel which is placed in the WCU. This differs from the real instrument, which will have a pupil-mask wheel in both imager arms as well as one in the common fore optics (CFO), and means that the functionality presented here can only be used with the WCU modes. The sky modes still use the SCAO PSFs as they always did.

```{code-cell} ipython3
import scopesim as sim
```

```{code-cell} ipython3
# Edit this path if you have a custom install directory, otherwise comment it out.
sim.link_irdb("../../../../")

# If you haven't got the instrument packages yet, uncomment the following line.
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

By default Scopesim loads one of the PPS masks with their corresponding PSF. The PSF files are stored on the Astar server in Vienna; they are automatically downloaded if they are not available locally (either in the download cache folder or in the subdirectory `./METIS_psfs`). For imaging in the LM band, do

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["wcu_img_lm"])
```

```{code-cell} ipython3
metis = sim.OpticalTrain(cmd)
```

We can inspect the two effects to check that they agree and to find out the location of the psf file that is used.

```{code-cell} ipython3
print(metis['pupil_masks'])
print(metis['psf'])
```

Change the WCU focal-plane mask to a pinhole to check that the correct PSF is used.

```{code-cell} ipython3
metis['wcu_source'].set_fpmask("pinhole_lm")
```

```{code-cell} ipython3
metis.observe()
```

```{code-cell} ipython3
from matplotlib import pyplot as plt
import numpy as np
```

```{code-cell} ipython3
implane = metis.image_planes[0].data
plt.imshow(implane - np.median(implane), norm='log', origin='lower')
plt.xlim(900, 1150)
plt.ylim(900, 1150);
```

## Changing the pupil mask
The pupil mask can be changed using the `change_mask` method of the pupil mask effect. Unfortunately, the PSF is not changed automatically due to a short-coming in ScopeSim (effects do not talk to each other...). ScopeSim does tell you, however, what you need to do:

```{code-cell} ipython3
metis['pupil_masks'].change_mask("APP-LM")
```

```{code-cell} ipython3
metis['psf'].update(pupil_mask="APP-LM")
```

```{code-cell} ipython3
print(metis['pupil_masks'])
print(metis['psf'])
```

```{code-cell} ipython3
metis.observe()
```

```{code-cell} ipython3
implane = metis.image_planes[0].data
plt.imshow(implane - np.median(implane), norm='log', origin='lower')
plt.xlim(900, 1150)
plt.ylim(900, 1150);
```

For each of the PPS PSFs there is a `WCU` variant, which does not include the ELT spiders:

```{code-cell} ipython3
metis['pupil_masks'].change_mask("PPS-LM")
metis['psf'].update(pupil_mask="PPS-LM_WCU")
```

```{code-cell} ipython3
metis.observe()
```

```{code-cell} ipython3
implane = metis.image_planes[0].data
plt.imshow(implane - np.median(implane), norm='log', origin='lower')
plt.xlim(900, 1150)
plt.ylim(900, 1150);
```

## A problem with spectroscopy
The PSF files (as provided by Roy van Boekel) have many extensions with the PSF computed at various wavelengths. This has uncovered a problem in the spectroscopic modes which results in a number of dark lines and pixels at wavelengths where Scopesim transitions from one PSF extension to the next (the segmentation in wavelength is evident by the ample output in the simulation below). This will hopefully be fixed soon.

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=["wcu_lss_n"])
metis = sim.OpticalTrain(cmd)
metis['wcu_source'].set_fpmask("pinhole_n")
```

```{code-cell} ipython3
metis.observe()
```

```{code-cell} ipython3
implane = metis.image_planes[0].data
plt.imshow(implane, origin='lower');
```

Note that the trace of the pinhole is not visible in this figure due to the high background. Subtracting a WCU_OFF simulation (after setting `metis['wcu_source'].set_bb_aperture(0.)`) would make it visible.
