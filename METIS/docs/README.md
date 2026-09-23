```{image} metis_scopesim_logo.png
:width: 600px
:alt: METIS + ScopeSim
:align: center
```

# METIS + ScopeSim

## Introduction

The METIS data simulator is based on the generic simulator ScopeSim, a
descendant of the older SimCado/SimMETIS interface. METIS itself is handled
as an instrument package containing configuration files for the various
instrument modes and data files describing the instrument components.

The simulator currently supports imaging and long-slit spectroscopy modes.
The LM-band high-resolution IFU (LMS) mode is under development.

```{note}
**Bug reports and help desk**

If you come across a bug or get stuck with ScopeSim or the METIS package,
please [open an issue on GitHub](https://github.com/AstarVienna/irdb/issues)
or contact us by email (see below).

**Your feedback is the only way we know** what needs to be
changed or improved with the package and the simulator.

Please always include the output of `scopesim.bug_report()` from your
installation.
```

## Downloading the METIS instrument package

Once ScopeSim is installed, download the METIS instrument package into your
working directory:

```python
import scopesim
scopesim.download_packages(["Armazones", "ELT", "METIS"])
```

This installs the packages into the subdirectory `./inst_pkgs/`.

Your working directory should look like this afterwards:

```
my_simulations/
├── <your notebook>.ipynb
└── inst_pkgs/
    ├── Armazones/
    ├── ELT/
    └── METIS/
        └── docs/
            └── example_notebooks/
                └── <notebook>.ipynb   ← copy to working dir before running
```

```{include} ../../docs/ScopeSim_guide.md
```

## Example notebooks

Find the notebooks locally in `inst_pkgs/METIS/docs/example_notebooks/`
after downloading the package, or download them from the
[GitHub repository](https://github.com/AstarVienna/irdb/tree/dev_master/METIS/docs/example_notebooks).

```{warning}
Run notebooks in your working directory, **not** inside `inst_pkgs/`.
Copy the desired notebook out first.
```

### Introductory notebooks

```{toctree}
:maxdepth: 1

example_notebooks/Introduction_to_Scopesim_for_METIS
example_notebooks/METIS_IFU-01-Source_cube
example_notebooks/METIS_IFU-02-Simulation
example_notebooks/METIS_WCU
```

### Scientific use-case notebooks

```{toctree}
:maxdepth: 1

example_notebooks/IMG_L_N-examples
example_notebooks/LSS-YSO_model_simulation
example_notebooks/LSS_AGN-01_preparation
example_notebooks/LSS_AGN-02_simulation
```

### Effect demonstration notebooks

These notebooks are in `docs/example_notebooks/demos/`.

```{toctree}
:maxdepth: 1
:glob:

example_notebooks/demos/*
```

### Instrument homepage

[METIS at Leiden Observatory](https://metis.strw.leidenuniv.nl/)
