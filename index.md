---
html_theme.sidebar_secondary.remove: true
---

```{image} docs/source/_static/logos/logo_irdb.PNG
:width: 600px
:alt: Instrument Reference Database
:align: center
```

# Instrument Reference Database

The **Instrument Reference Database (IRDB)** contains the instrument-specific
configuration and data files used by the
[ScopeSim](https://scopesim.readthedocs.io/en/latest/) astronomical instrument
simulator.

Each instrument package below ships with example notebooks, mode configuration
files, and the component data (filters, PSFs, detector layouts, etc.) needed to
run realistic end-to-end simulations.

## Available Instruments

::::{grid} 1 2 3 3
:gutter: 3

:::{grid-item-card} MICADO
:img-top: MICADO/docs/micado_scopesim_logo.png
:link: MICADO/docs/README
:link-type: doc

**Near-infrared camera for the ELT**

Supports MCAO (4 mas) and SCAO (1.5 mas / 4 mas) imaging modes.
:::

:::{grid-item-card} METIS
:img-top: METIS/docs/metis_scopesim_logo.png
:link: METIS/docs/README
:link-type: doc

**Thermal-infrared imager and spectrograph for the ELT**

Supports imaging and long-slit spectroscopy. LMS IFU mode in development.
:::

:::{grid-item-card} MOSAIC
:img-top: MOSAIC/docs/mosaic_scopesim_logo.png
:link: MOSAIC/docs/README
:link-type: doc

**Multi-object spectrograph for the ELT**

12 observation modes across VIS/NIR MOS and NIR mIFU.
:::

::::

## All Instrument Packages

| Location  | Telescope | Instrument                   | Documented |
|-----------|-----------|------------------------------|------------|
| Armazones | ELT       | [MICADO](MICADO/docs/README) | ✓          |
| Armazones | ELT       | [METIS](METIS/docs/README)   | ✓          |
| Armazones | ELT       | [MOSAIC](MOSAIC/docs/README) | ✓          |
| Paranal   | VLT       | HAWKI                        |            |
| LFOA      | -         | -                            |            |

```{toctree}
:hidden:
:maxdepth: 2
:caption: Instruments

METIS + ScopeSim <METIS/docs/README>
MICADO + ScopeSim <MICADO/docs/README>
MOSAIC + ScopeSim <MOSAIC/docs/README>
```
