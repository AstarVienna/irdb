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

# Demonstration of spectral (grating) efficiency

This notebook demonstrates and tests the `SpectralEfficiency` effect for the METIS long-slit spectroscopic modes. Lacking real data, the grating effciencies used here (and available in the irdb) are pure fantasy.

```{code-cell} ipython3
import scopesim as sim

sim.bug_report()

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../../"
```

```{code-cell} ipython3
import numpy as np
from astropy.io import fits
from astropy.io import ascii as ioascii
from astropy import units as u
from matplotlib import pyplot as plt
```

If you haven't got the instrument packages yet, uncomment the following cell.

```{code-cell} ipython3
# sim.download_packages(["METIS", "ELT", "Armazones"])
```

## Source -- constant spectrum

```{code-cell} ipython3
from synphot import SourceSpectrum, Empirical1D
from scopesim_templates.micado import flatlamp
```

```{code-cell} ipython3
lam = np.linspace(2.8, 18, 2048)
flux = 0.1 * np.ones_like(lam)
spec = SourceSpectrum(Empirical1D, points = lam * u.um, lookup_table=flux)

src = flatlamp()
src.spectra[0] = spec
```

## L band

```{code-cell} ipython3
cmd_l = sim.UserCommands(use_instrument='METIS', set_modes=['lss_l'])

metis_l = sim.OpticalTrain(cmd_l)

metis_l['psf'].include = False                # PSF is not necessary for slit-filling source
metis_l['skycalc_atmosphere'].include = False # sky lines obscure flat spectrum 
```

Observe the source with and without the grating efficiency. The ratio between the two results (we look at the image plane, which is noise free) shows directly the efficiency.
As long as no realistic data are available, the efficiency effect is turned off by default and has to be included explicitely.

```{code-cell} ipython3
metis_l['grating_efficiency'].include  = True
metis_l.observe(src)
sim_l_with_effic = metis_l.image_planes[0].data
```

```{code-cell} ipython3
metis_l['grating_efficiency'].include = False
metis_l.observe(src, update=True)
sim_l_without_effic = metis_l.image_planes[0].data
```

```{code-cell} ipython3
ratio_l = sim_l_with_effic / sim_l_without_effic
plt.figure(figsize=(15, 5))
plt.subplot(131)
plt.imshow(sim_l_with_effic, origin='lower')
plt.title("L band, with grating efficiency")
plt.subplot(132)
plt.imshow(sim_l_without_effic, origin='lower')
plt.title("L band, without grating efficiency")
plt.subplot(133)
plt.imshow(ratio_l, origin='lower')
plt.title("L band, ratio");
```

```{code-cell} ipython3
plt.plot((sim_l_with_effic / sim_l_without_effic)[:, 1000]);
```

## M band

```{code-cell} ipython3
cmd_m = sim.UserCommands(use_instrument='METIS', set_modes=['lss_m'])
metis_m = sim.OpticalTrain(cmd_m)
```

```{code-cell} ipython3
metis_m['psf'].include = False                # PSF is not necessary for slit-filling source
metis_m['skycalc_atmosphere'].include = False # sky lines obscure flat spectrum 
```

```{code-cell} ipython3
metis_m['grating_efficiency'].include  = True
metis_m.observe(src, update=True)
sim_m_with_effic = metis_m.image_planes[0].data
```

```{code-cell} ipython3
metis_m['grating_efficiency'].include = False
metis_m.observe(src, update=True)
sim_m_without_effic = metis_m.image_planes[0].data
```

```{code-cell} ipython3
ratio_m = sim_m_with_effic / sim_m_without_effic
plt.figure(figsize=(15, 5))
plt.subplot(131)
plt.imshow(sim_m_with_effic, origin='lower')
plt.title("M band, with grating efficiency")
plt.subplot(132)
plt.imshow(sim_m_without_effic, origin='lower')
plt.title("M band, with grating efficiency")
plt.subplot(133)
plt.imshow(ratio_m, origin='lower')
plt.title("M band, ratio");
```

```{code-cell} ipython3
plt.plot(ratio_m[:, 1000]);
```

## N band

```{code-cell} ipython3
cmd_n = sim.UserCommands(use_instrument='METIS', set_modes=['lss_n'])
metis_n = sim.OpticalTrain(cmd_n)
```

```{code-cell} ipython3
metis_n['psf'].include = False                # PSF is not necessary for slit-filling source
metis_n['skycalc_atmosphere'].include = False # sky lines obscure flat spectrum 
```

```{code-cell} ipython3
metis_n['grating_efficiency'].include  = True
metis_n.observe(src, update=True)
sim_n_with_effic = metis_n.image_planes[0].data
```

```{code-cell} ipython3
metis_n['grating_efficiency'].include = False
metis_n.observe(src, update=True)
sim_n_without_effic = metis_n.image_planes[0].data
```

```{code-cell} ipython3
ratio_n = sim_n_with_effic / sim_n_without_effic
plt.figure(figsize=(15, 5))
plt.subplot(131)
plt.imshow(sim_n_with_effic, origin='lower')
plt.title("N band, with grating efficiency")
plt.subplot(132)
plt.imshow(sim_n_without_effic, origin='lower')
plt.title("N band, with grating efficiency")
plt.subplot(133)
plt.imshow(ratio_n, origin='lower')
plt.title("N band, ratio");
```

```{code-cell} ipython3
plt.plot(ratio_n[:, 1000]);
```
