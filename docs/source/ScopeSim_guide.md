## ScopeSim quickstart guide

### Installing ScopeSim

#### Install `scopesim` in your python environment.

The easiest way to install Scopesim is to use `pip` from the command line:

```bash
pip install scopesim
```

If you want to upgrade an existing installation, do

```bash
pip install -U scopesim
```

#### Optional: Create a working directory where you want to run simulations, e.g.:

```bash
mkdir ~/path/to/playing_with_scopesim/
cd ~/path/to/playing_with_scopesim
```

#### In your favourite python environment (e.g. `ipython`, `jupyter notebook` or a script), scopesim is loaded by

```python
import scopesim
```

We usually follow the convention of using the shorter alias `sim` in most of our documentation:

```python
import scopesim as sim
```

```{tip}
Scopesim has a utility function `sim.bug_report()` which checks a number of other python packages required by scopesim and reports their version numbers. The output of this command should be included in any bug report or question submitted to the scopesim team.
```

### Installing instrument packages

Scopesim is a general simulation framework. In order to simulate observations with any particular instrument, you will have to load an instrument package, as well as packages describing the telescope and observatory location (the latter is important for the atmospheric conditions). In the case of METIS, the packages can be downloaded with 

```python
sim.download_packages(["METIS", "ELT", "Armazones"])
```

```{hint}
:class: margin

It is not generally necessary to download the instrument packages every time you run a simulation!
Usually the best practise is to download the packages you need once and then run everything from the same folder or tell ScopeSim where to find the installed packages (see below).

ScopeSim does come with a builtin automatic check for new versions of the packages you're using, but this functionality is not always reliable, so if you're suspecting to have an outdated version, it's best to just run the download command again.
```

By default, scopesim looks for the packages in the subdirectory `inst_pkgs` of the current working directory. The download command will install them there, so there should be no problem.  

It is possible to install the packages elsewhere; if you do that you will have to declare to scopesim where they are. This can be done by setting

```python
sim.rc.__config__["!SIM.file.local_packages_path"] = "/path/to/inst_pgks"
```

```{tip}
If you encounter the error `File cannot be found: default.yaml` when calling `sim.UserCommands` (see below), either call `sim.download_package` from the working directory or set the `local_packages_path` as just explained.
```

We suggest following the default scheme, because keeping the instrument packages together with the input and output data of scopesim makes it easier later to reconstruct the conditions under which a simulation was run. 

The command `sim.list_packages()` lists all packages that are available for download, as well as those that are already installed.
