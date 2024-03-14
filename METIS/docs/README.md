# METIS + ScopeSim

```{image} metis_scopesim_logo.png
:alt: METIS + ScopeSim
:width: 600px
```

## Introduction

The METIS data simulator is based on the generic simulator software Scopesim, a descendant of the older SimCado/SimMETIS interface. METIS itself is handled as an instrument package that contains configuration files for the various instrument modes as well as data files describing the components of the instruments.
The new METIS data simulator currently supports the imaging and long-slit modes. The LM-band high-resolution IFU (LMS) mode will be offered soon.

## Prerequisites

- A working installation of a recent Python version
- A working installation of Jupyter if you want to run the simulator from notebooks. This is necessary to run the example notebooks contained in the instrument package.
- A working installation of the Python package installer pip

```{note}
If you come across a bug or get stuck with a certain aspect of ScopeSim or the METIS package, please get in touch with us (email addresses below).

**Your feedback is the only way we know** what needs to be changed/improved with the package and the simulator.

Please always provide the output of the command `scopesim.bug_report()` run on your installation.
```

## Installation & setup

This is a short overview of the installation and setup procedure; for a more detailed presentation see [Introduction_to_Scopesim_for_METIS](example_notebooks/Introduction_to_Scopesim_for_METIS).

1. Install `scopesim` in your python environment:

    ```bash
    pip install scopesim
    ```

    To upgrade an existing installation do:

    ```bash
    pip install -U scopesim
    ```

2. Create a working directory where you want to run simulations, e.g.:

    ```bash
    mkdir ~/path/to/playing_with_scopesim/
    cd ~/path/to/playing_with_scopesim
    ```

3. Install relevant irdb packages into this directory:

    ```python
    import scopesim
    scopesim.download_packages(["METIS", "ELT", "Armazones"])
    ```

    This will install the packages in the subdirectory `./inst_pkgs`.

4. The METIS package includes a number of tutorial notebooks in the directory `./inst_pkgs/METIS/docs/example_notebooks/` (see [Python notebooks](#py-nbs)).

    Copy notebooks to the working directory (i.e. `./`) to run them.:

    ```bash
    cp ./inst_pkgs/METIS/docs/example_notebooks/<Notebook-Name.ipynb> .
    ```

5. In a terminal, execute the notebook by calling::

    ```bash
    jupyter notebook <filename.ipynb>
    ```

6. Follow instructions and explanations in the notebook. Some notebooks use example data; the commands to download these data from the scopesim server are included in the notebooks.

You can then edit the notebooks and use them as a starting point for your own simulations.

(py-nbs)=
## Python notebooks

These notebooks can be found either:

- *locally* in the METIS instrument package in `docs/example_notebooks`, or
- *download* in the [METIS/docs section of the IRDB Github repository](https://github.com/AstarVienna/irdb/tree/master/METIS/docs/example_notebooks)


```{warning}
Notebooks should be run in your working directory, **NOT** directly in the `docs/example_notebooks` folder. Please copy the desired notebook out of this folder.
```

Ideally your folder structure should look like this::

```
working-dir
├─ <desired notebook>.iypnb
│
└─ inst_pkgs
  ├─ METIS
  │  └─ docs
  │     └─ example_notebooks
  │        └─ <desired notebook>.iypnb      # copy out to working-dir
  ├─ ELT
  └─ Armazones
```

```{toctree}
:maxdepth: 2
:caption: debug

example_notebooks/testnotebook
example_notebooks/testnotebook2
example_notebooks/testnotebook3
```

```{toctree}
:maxdepth: 2
:caption: Introductory overview of how to run simulations in ScopeSim

example_notebooks/Introduction_to_Scopesim_for_METIS
example_notebooks/IMG_L_N-examples
example_notebooks/IFU-examples
example_notebooks/RawHeaders
```

```{toctree}
:maxdepth: 2
:caption: Scientific use-case notebooks

example_notebooks/LSS_AGN-01_preparation
example_notebooks/LSS_AGN-02_simulation
example_notebooks/LSS-YSO_model_simulation
```

```{toctree}
:maxdepth: 2
:caption: Notebooks on individual effects

example_notebooks/demos/demo_adc_wheel
example_notebooks/demos/demo_auto_exposure
example_notebooks/demos/demo_chopping_and_nodding
example_notebooks/demos/demo_detector_modes
example_notebooks/demos/demo_filter_wheel
example_notebooks/demos/demo_grating_efficiency
example_notebooks/demos/demo_lss_simple
example_notebooks/demos/demo_metis_lms_efficiency
example_notebooks/demos/demo_rectify_traces
example_notebooks/demos/demo_slit_wheel
```

## Documentation and useful references

- [ScopeSim documentation](https://scopesim.readthedocs.io/en/latest/)
- [Sky Object Templates documentation](https://scopesim-templates.readthedocs.io/en/latest/)
- [METIS homepage](https://metis.strw.leidenuniv.nl/)
- For experts: GitHub repositories:

  + simulator package [ScopeSim](https://github.com/AstarVienna/scopesim)
  + instrument-specific packages [IRDB](https://github.com/AstarVienna/irdb)

## Contact points

[ScopeSim Slack](https://join.slack.com/t/scopesim/shared_invite/zt-143s42izo-LnyqoG7gH5j~aGn51Z~4IA)

### Email

- scopesim@univie.ac.at
- kieran.leschinski@univie.ac.at
