## Prerequisites

- A working installation of Python 3.8 or newer
- `pip` (the Python package installer)
- Jupyter, if you want to run the example notebooks (recommended)

## Installing ScopeSim

Install the latest release from PyPI:

```bash
pip install scopesim
```

To upgrade an existing installation:

```bash
pip install -U scopesim
```

## Setting up a working directory

Create a dedicated directory where your simulation notebooks will live and
where the instrument packages will be downloaded:

```bash
mkdir ~/path/to/my_simulations
cd ~/path/to/my_simulations
```

## Running the example notebooks

The instrument package ships tutorial notebooks inside
`inst_pkgs/<INSTRUMENT>/docs/example_notebooks/`.
Copy the desired notebook out of that folder before running it — notebooks
should **not** be run in-place, as their output would modify the package files.

```bash
cp ./inst_pkgs/<INSTRUMENT>/docs/example_notebooks/<Notebook.ipynb> .
jupyter notebook <Notebook.ipynb>
```

## Documentation and useful references

- [ScopeSim documentation](https://scopesim.readthedocs.io/en/latest/)
- [ScopeSim Templates documentation](https://scopesim-templates.readthedocs.io/en/latest/)
- GitHub repositories:
  - [ScopeSim (simulator engine)](https://github.com/AstarVienna/scopesim)
  - [IRDB (instrument packages)](https://github.com/AstarVienna/irdb)

## Contact and support

- [ScopeSim Slack](https://join.slack.com/t/scopesim/shared_invite/zt-143s42izo-LnyqoG7gH5j~aGn51Z~4IA)
- [GitHub Issues](https://github.com/AstarVienna/irdb/issues)
- Email: scopesim@univie.ac.at · kieran.leschinski@univie.ac.at
