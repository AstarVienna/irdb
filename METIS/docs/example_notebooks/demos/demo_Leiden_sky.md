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

```{code-cell} ipython3
from matplotlib import pyplot as plt
import numpy as np
from astropy import units as u
```

METIS AIT activities in Leiden will use bespoke relay optics to observe the sky above the integration hall with METIS. Scopesim can simulate these observations for the spectroscopic modes. Emission and transmission spectra for the sky above Leiden were calculated by Wolfgang Kausch for 50 values of precipital water vapour (PWV). The data are stored on the Astar server in Vienna and will be downloaded the first time you use them.

```{code-cell} ipython3
import scopesim as sim

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.link_irdb("../../../../")

# If you haven't got the instrument packages yet, uncomment the following line.
#sim.download_packages(["METIS"])
```

The available modes using the Leiden sky are `leiden_lss_l`, `leiden_lss_m`, `leiden_lss_n` and `leiden_lms`. We will simulate an LSS_M observation, using a PWV value of 10 mm. 

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=['leiden_lss_m'])
cmd["!ATMO.pwv"] = 10       # could also use properties={"!ATMO.pwv": 10} in UserCommands
```

```{code-cell} ipython3
metis = sim.OpticalTrain(cmd)
```

```{code-cell} ipython3
metis.effects.pprint_all()
```

The `leiden_` modes replace the `ELT` and `Armazones` packages with two effects, `leiden_sky`, which creates the background source using the atmospheric spectra for the selected PWV, and `telescope`, which models the relay optics. 

`telescope` has no user-modifiable parameters; its configuration can be inspected as follows:

```{code-cell} ipython3
metis['telescope'].table
```

The atmospheric emission is provided by the effect `leiden_sky`. It has one parameter, the precipitable water vapour:

```{code-cell} ipython3
print(metis["leiden_sky"])
```

The transmission and emission spectra can be plotted as follows:

```{code-cell} ipython3
metis['leiden_sky'].plot(which="te", wavelength=np.linspace(3, 6, 1001)*u.um);
```

An observation is done as usual with the `.observe()` method. No `Source` object is required.

```{code-cell} ipython3
metis.observe()
```

```{code-cell} ipython3
plt.imshow(metis.image_planes[0].data, norm="log")
```

```{code-cell} ipython3
plt.plot(metis.image_planes[0].data[:, 1000])
plt.xlabel("Row number (~ wavelength)")
plt.ylabel("Photons/second (ImagePlane)");
```

The plots show the `ImagePlane`. After a `readout`, the `metis[spectral_traces].rectify_traces()` method could be used to show the simulation on a linear wavelength scale.

+++

**Not yet**: The `leiden_sky` effect (or rather the underlying `AtmoLibraryTERCurve` effect) has an update method, which allows to change the PWV value. This does not work yet! We recommend creating a new `OpticalTrain` after setting `cmd["!ATMO.pwv"]` to a new value. This will hopefully be fixed soon.

```{code-cell} ipython3
metis['leiden_sky'].update(pwv=50)
metis['leiden_sky'].plot(which="te", wavelength=np.linspace(3, 6, 1001)*u.um);
```

# Comparison to Armazones/ELT
The following compares the Leiden spectrum with a spectrum of the Armazones sky and METIS at the ELT.

```{code-cell} ipython3
cmd_elt = sim.UserCommands(use_instrument="METIS", set_modes=["lss_m"])
```

```{code-cell} ipython3
elt = sim.OpticalTrain(cmd_elt)
```

```{code-cell} ipython3
elt.observe()
```

```{code-cell} ipython3
plt.plot(elt.image_planes[0].data[:, 1000]/(36.9**2 - 10.95**2) * (0.66**2 * np.cos(np.pi/4)), label="Armazones")
#plt.plot(elt.image_planes[0].data[:, 1000] / 975.2347899768369 * 0.34, label="Armazones 2")
plt.plot(metis.image_planes[0].data[:, 1000], label="Leiden")
plt.xlabel("Row number (~ wavelength)")
plt.ylabel("Photons/second (ImagePlane)")
#plt.ylim(0, 10)
plt.legend();
```

```{code-cell} ipython3
leiden = metis['leiden_sky']
armazones = elt["skycalc_atmosphere"]
```

```{code-cell} ipython3
lam = np.linspace(4, 5, 1001)*u.um
f_leiden = leiden.emission(lam)
f_armazones = armazones.emission(lam)
```

```{code-cell} ipython3
plt.plot(lam, f_armazones, label="Armazones", lw=1)
plt.plot(lam, f_leiden, label="Leiden", lw=1)
#plt.semilogy()
plt.xlabel("Wavelength [um]")
plt.ylabel("PHOTLAM")
plt.xlim(4.6, 4.8)
plt.legend();
```

```{code-cell} ipython3
lam_leiden = leiden.surface.emission.waveset.to(u.um)
lam_armazones = armazones.surface.emission.waveset.to(u.um)
```

```{code-cell} ipython3
plt.plot(lam_armazones, armazones.surface.emission(lam_armazones), label="Armazones")
plt.plot(lam_leiden, leiden.surface.emission(lam_leiden), label="Leiden")
plt.xlim(3.2, 3.4)
plt.ylim(0, 0.5)
plt.legend()
```

```{code-cell} ipython3
rlam_leiden = lam_leiden[(lam_leiden > 4.6*u.um) * (lam_leiden < 4.8*u.um)] 
```

```{code-cell} ipython3
leiden.emission.integrate(wavelengths=rlam_leiden)
```

```{code-cell} ipython3
rlam_arm = lam_armazones[(lam_armazones > 4.6*u.um) * (lam_armazones < 4.8*u.um)]
```

```{code-cell} ipython3
armazones.emission.integrate(wavelengths=rlam_arm)
```

As expected, the Leiden sky is brighter (in the M band) than the sky above Armazones. Note that this is just an exemplary comparison, and we have not tried to match the atmospheric parameters in much detail. A similar exercise in the L band results in Armazones being brighter than Leiden. It should be borne in mind that the Leiden sky model only includes atmospheric emission and neglects scattered moon light, zodiacal light and other effects that are taken into account in the more sophisticated `skycalc` model used for Armazones.
