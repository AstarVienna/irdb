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

# Test ADC wheel

This notebook demonstrates how to use the various atmospheric dispersion correctors in METIS. Note that the action of an adc is currently restricted to a transmission loss. The implementation of the geometric differential refraction residuals will follow at a later stage.

```{code-cell} ipython3
import scopesim as sim
sim.bug_report()

# Edit this path if you have a custom install directory, otherwise comment it out.
sim.link_irdb("../../../../") 
```

```{code-cell} ipython3
import numpy as np
```

If you haven't got the instrument packages yet, uncomment the following cell

```{code-cell} ipython3
# sim.download_packages(["METIS", "ELT", "Armazones"]) 
```

```{code-cell} ipython3
cmd = sim.UserCommands(use_instrument="METIS", set_modes=['img_lm'])
```

The ADC to use is defined by `"!OBS.adc"`. This can be set to `false` when no ADC is in the path. The default for LM band imaging is

```{code-cell} ipython3
cmd["!OBS.adc"]
```

```{code-cell} ipython3
metis = sim.OpticalTrain(cmd)
```

The effect `metis['adc_wheel']` works the same way as e.g. `metis['filter_wheel']`. The following ADCs are now available (yes, there's only one) and can be selected with `metis['adc_wheel'].change_adc()` as demonstrated below.

```{code-cell} ipython3
metis['adc_wheel'].get_table()
```

Run a simulation with the ADC in the path (`observe()` without a source observe empty sky):

```{code-cell} ipython3
metis.observe()
implane_adc = metis.image_planes[0].data
```

Now remove the ADC from the path by changing to `False`. Run the simulation without the ADC:

```{code-cell} ipython3
metis['adc_wheel'].change_adc(False)
```

```{code-cell} ipython3
metis.observe()
implane_no_adc = metis.image_planes[0].data
```

Compare the image plane simulated with and without the ADC. The ratio should be equal to the throughput of the ADC (90 per cent):

```{code-cell} ipython3
med_adc = np.median(implane_adc)
med_no_adc = np.median(implane_no_adc)
print("With ADC:    {:.1f}".format(np.median(med_adc)))
print("Without ADC: {:.1f}".format(np.median(med_no_adc)))
print("Ratio:       {:.1f}".format(med_adc/med_no_adc))
```
