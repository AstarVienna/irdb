```{image} micado_scopesim_logo.png
:width: 600px
:alt: MICADO + ScopeSim
:align: center
```

# MICADO + ScopeSim

## Introduction

A MICADO data simulator is being developed as part of the generic simulator
ScopeSim, a descendant of the older SimCADO software. MICADO is the
near-infrared camera for the ELT and supports both MCAO (4 mas) and SCAO
(1.5 mas and 4 mas) imaging modes.

```{note}
**Bug reports and help desk**

If you come across a bug or get stuck with ScopeSim or the MICADO package,
please [open an issue on GitHub](https://github.com/AstarVienna/irdb/issues)
or contact us by email (see below).

**Your feedback is the only way we know** what needs to be
changed or improved with the package and the simulator.

Please always include the output of `scopesim.bug_report()` from your
installation.
```

## Downloading the MICADO instrument package

Once ScopeSim is installed, download the MICADO instrument package into your
working directory:

```python
import scopesim
scopesim.download_packages(["Armazones", "ELT", "MICADO"])
```

This installs the packages into the subdirectory `./inst_pkgs/`.

Your working directory should look like this afterwards:

```
my_simulations/
├── <your notebook>.ipynb
└── inst_pkgs/
    ├── Armazones/
    ├── ELT/
    └── MICADO/
        └── docs/
            └── example_notebooks/
                └── <notebook>.ipynb   ← copy to working dir before running
```

```{include} ../../docs/ScopeSim_guide.md
```

## Example notebooks

Download the notebooks from the
[GitHub repository](https://github.com/AstarVienna/irdb/tree/dev_master/MICADO/docs/example_notebooks)
or find them locally in `inst_pkgs/MICADO/docs/example_notebooks/` after
downloading the package.

```{warning}
Run notebooks in your working directory, **not** inside `inst_pkgs/`.
Copy the desired notebook out first.
```

### Scientific use-case notebooks

```{toctree}
:maxdepth: 1

example_notebooks/1_scopesim_MCAO_4mas_galaxy
example_notebooks/2_scopesim_SCAO_1.5mas_astrometry
example_notebooks/3_scopesim_SCAO_4mas_fv-psf
example_notebooks/MICADO_FAQs
```

| Notebook | Description |
|----------|-------------|
| `1_scopesim_MCAO_4mas_galaxy` | MCAO 4 mas imaging of a galaxy |
| `2_scopesim_SCAO_1.5mas_astrometry` | SCAO 1.5 mas astrometry use case |
| `3_scopesim_SCAO_4mas_fv-psf` | SCAO 4 mas field-varying PSF |
| `MICADO_FAQs` | Frequently asked questions |

## Validation

The table below shows limiting-magnitude test results (minimum S/N = 5).
Green = passed, yellow = expected deviation, red = unexpected failure.
**Click** a row to see the test plot.

```{eval-rst}
.. validation-report:: ./MICADO/test_micado/validation_results.xml
```

The test code lives in the
[MICADO/test_micado/](https://github.com/AstarVienna/irdb/tree/dev_master/MICADO/test_micado/)
folder on GitHub.
