```{image} mosaic_scopesim_logo.png
:width: 600px
:alt: MOSAIC + ScopeSim
:align: center
```

# MOSAIC + ScopeSim

## Introduction

The MOSAIC ETC is built on the generic simulator ScopeSim. MOSAIC is handled
as an instrument package containing configuration files for the various
instrument modes and data files describing the instrument components.

MOSAIC supports twelve observation modes across visual (VIS) and near-infrared
(NIR) multi-object spectroscopy and NIR integral-field unit (mIFU) operations.

```{note}
**Bug reports and help desk**

If you come across a bug or get stuck with ScopeSim or the MOSAIC package,
please [open an issue on GitHub](https://github.com/AstarVienna/irdb/issues)
or contact us by email (see below).

**Your feedback is the only way we know** what needs to be
changed or improved with the package and the simulator.

Please always include the output of `scopesim.bug_report()` from your
installation.
```

## Downloading the MOSAIC instrument package

Once ScopeSim is installed, download the MOSAIC instrument package into your
working directory:

```python
import scopesim
scopesim.download_packages(["Armazones", "ELT", "MOSAIC"])
```

This installs the packages into the subdirectory `./inst_pkgs/`.

Your working directory should look like this afterwards:

```
my_simulations/
├── <your notebook>.ipynb
└── inst_pkgs/
    ├── Armazones/
    ├── ELT/
    └── MOSAIC/
        └── docs/
            └── example_notebooks/
                └── <notebook>.ipynb   ← copy to working dir before running
```

```{include} ../../docs/ScopeSim_guide.md
```

## Example notebooks

Find the notebooks locally in `inst_pkgs/MOSAIC/docs/example_notebooks/`
after downloading the package, or download them from the
[GitHub repository](https://github.com/AstarVienna/irdb/tree/dev_master/MOSAIC/docs/example_notebooks).

```{warning}
Run notebooks in your working directory, **not** inside `inst_pkgs/`.
Copy the desired notebook out first.
```

### Introductory notebooks

| Notebook | Description |
|----------|-------------|
| [`MOSAIC_demo.ipynb`](example_notebooks/MOSAIC_demo.ipynb) | Introductory overview of how to run MOSAIC simulations in ScopeSim |

### Instrument homepage

[MOSAIC at mosaic-elt.eu](https://mosaic-elt.eu/index.php/instrument/)
