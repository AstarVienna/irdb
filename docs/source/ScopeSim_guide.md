## ScopeSim quickstart guide

### Installing ScopeSim

The following basic steps are required to use ScopeSim:

#### 1. Install `scopesim` in your python environment

The easiest way to install Scopesim is to use `pip` from the command line:

```bash
pip install scopesim
```

If you want to upgrade an existing installation, do

```bash
pip install -U scopesim
```

#### 2. Optional: Create a working directory to run simulations from

e.g.:

```bash
mkdir ~/path/to/playing_with_scopesim/
cd ~/path/to/playing_with_scopesim
```

#### 3. Import the `scopesim` package

In your favourite python environment (e.g. `ipython`, `jupyter notebook` or a script), ScopeSim is loaded by

```python
import scopesim
```

We usually follow the convention of using the shorter alias `sim` in most of our documentation:

```python
import scopesim as sim
```

```{tip}
Scopesim has a utility function `sim.bug_report()` which checks a number of other python packages required by ScopeSim and reports their version numbers. The output of this command should be included in any bug report or question submitted to the ScopeSim team.
```

### Installing instrument packages

Scopesim is a general simulation framework. In order to simulate observations with any particular instrument, you will have to load an instrument package, as well as packages describing the telescope and observatory location (the latter is important for the atmospheric conditions).

```{hint}
:class: margin

It is not generally necessary to download the instrument packages every time you run a simulation!
Usually the best practise is to download the packages you need once and then run everything from the same folder or tell ScopeSim where to find the installed packages (see below).

ScopeSim does come with a builtin automatic check for new versions of the packages you're using, but this functionality is not always reliable, so if you're suspecting to have an outdated version, it's best to just run the download command again.
```

In the case of e.g. METIS, the packages can be downloaded with:

```python
sim.download_packages(["Armazones", "ELT", "METIS"])
```

For some instruments that optionally work together, it is necessary to download both individually, e.g. in the case of MICADO and MORFEO:

```python
sim.download_packages(["Armazones", "ELT", "MORFEO", "MICADO"])
```

In general, the structure usually is `["<site>", "<telescope>", "<instrument(s)>"]`, although the order of the packages does not matter at all, as long as all relevant ones are present. If you're running simulations for multiple instruments or telescopes, you can simply download them all in one command.

By default, ScopeSim looks for the packages in the subdirectory `inst_pkgs` of the current working directory. The download command will install them there, so there should be no problem.  

It is possible to install the packages elsewhere; if you do that you will have to declare to ScopeSim where they are. This can be done by setting

```python
sim.rc.__config__["!SIM.file.local_packages_path"] = "/path/to/inst_pgks"
```

```{tip}
If you encounter the error `File cannot be found: default.yaml` when calling `sim.UserCommands` (see below), either call `sim.download_package` from the working directory or set the `local_packages_path` as just explained.
```

We suggest following the default scheme, because keeping the instrument packages together with the input and output data of ScopeSim makes it easier later to reconstruct the conditions under which a simulation was run. 

The command `sim.list_packages()` lists all packages that are available for download, as well as those that are already installed.
