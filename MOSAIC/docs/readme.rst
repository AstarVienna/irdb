.. |pic1| image:: mosaic_scopesim_logo.png
   :width: 600px
   :alt: MOSAIC + ScopeSim

|pic1|
======

Introduction
------------
The MOSAIC ETC is built on the generic simulator software Scopesim.
MOSAIC itself is handled as an instrument package that contains configuration files for the various instrument modes as well as data files describing the components of the instruments.


Prerequisites
-------------

- A working installation of a recent Python version
- A working installation of Jupyter if you want to run the simulator from notebooks. This is necessary to run the example notebooks contained in the instrument package.
- A working installation of the Python package installer ``pip``

.. note::

   If you come across a bug or get stuck with a certain aspect of ScopeSim or
   the MOSAIC package, please get in touch with us (GitHub issue, or email addresses below).

   **Your feedback is the only way we know** what needs to be changed/improved
   with the package and the simulator.

   Please always provide the output of the command ``scopesim.bug_report()`` run on your installation.


Installation & setup
--------------------

This is a short overview of the installation and setup procedure; for a more detailed presentation see `Introduction_to_Scopesim_for_MOSAIC <example_notebooks/Introduction_to_Scopesim_for_MOSAIC.ipynb>`_.

1. Install ``scopesim`` in your python environment::

    $ pip install scopesim

   To upgrade an existing installation do::

    $ pip install -U scopesim

2. Create a working directory where you want to run simulations, e.g.::

    $ mkdir ~/path/to/playing_with_scopesim/
    $ cd ~/path/to/playing_with_scopesim

3. Install relevant irdb packages into this directory::

    $ python
    >> import scopesim
    >> scopesim.download_packages(["MOSAIC", "ELT", "Armazones"])

   This will install the packages in the subdirectory ``./inst_pkgs``.

4. The MOSAIC package includes a number of tutorial notebooks in the directory ``./inst_pkgs/MOSAIC/docs/example_notebooks/`` (see `Python notebooks`_).

   Copy notebooks to the working directory (i.e. ``./``) to run them.::

    $ cp ./inst_pkgs/MOSAIC/docs/example_notebooks/<Notebook-Name.ipynb> .

5. In a terminal, execute the notebook by calling::

    $ jupyter notebook <filename.ipynb>

6. Follow instructions and explanations in the notebook. Some notebooks use example data; the commands to download these data from the scopesim server are included in the notebooks.

You can then edit the notebooks and use them as a starting point for your own simulations.


Python notebooks
----------------

These notebooks can be found either:

- [locally] in the MOSAIC instrument package in ``docs/example_notebooks``, or
- [download] in the `MOSAIC/docs section of the IRDB Github repository <https://github.com/AstarVienna/irdb/tree/master/MOSAIC/docs/example_notebooks>`_


.. warning::
   Notebooks should be run in your working directory, **NOT** directly in the
   ``docs/example_notebooks`` folder. Please copy the desired notebook out of
   this folder.

Ideally your folder structure should look like this::

    working-dir
    |- <desired notebook>.iypnb
    |
    |- inst_pkgs
      |- MOSAIC
      |  |- docs
      |     |- example_notebooks
      |        |- <desired notebook>.iypnb      # copy out to working-dir
      |- ELT
      |- Armazones


Introductory notebooks
++++++++++++++++++++++

.. list-table::
   :widths: 25 75
   :width: 900px
   :header-rows: 1

   * - Name
     - Description
   * - | `MOSAIC_demo.ipynb <example_notebooks/MOSAIC_demo.ipynb>`_
     - Introductory overview of how to run simulations in Scopesim

Documentation and useful references
-----------------------------------

- `ScopeSim documentation <https://scopesim.readthedocs.io/en/latest/>`_
- `Sky Object Templates documentation <https://scopesim-templates.readthedocs.io/en/latest/>`_
- `MOSAIC homepage <https://mosaic-elt.eu/index.php/instrument/>`_
- For experts: GitHub repositories:

  + `simulator package ScopeSim <https://github.com/AstarVienna/scopesim>`_
  + `instrument-specific packages irdb <https://github.com/AstarVienna/irdb>`_.


Contact points
--------------
`ScopeSim Slack <https://join.slack.com/t/scopesim/shared_invite/zt-143s42izo-LnyqoG7gH5j~aGn51Z~4IA>`_

Email:

- scopesim@univie.ac.at
- kieran.leschinski@univie.ac.at
