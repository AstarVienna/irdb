METIS + ScopeSim
================

Introduction
------------
For the preparation of FDR documentation, a new METIS data simulator is being developed that is technically an instrument-package for the generic simulator ScopeSim, a descendant of the older SimCado/SimMETIS interface.
The new METIS data simulator currently supports the imaging and long-slit modes (tbc) and the LMS mode is planned to be offered soon, too.
The old data simulator, SimMETIS v0.3, can still be used for simulating LMS observations.

Prerequisites
-------------

- A working installation of Python 3.6 or newer
- A working installation of Jupyter notebooks if you want to run the simulator from notebooks, i.e. using a graphical interactive interface, rather than just the terminal or scripts (highly recommended)
- A working installation of the Python package installer pip

.. note:: Bug reports and help-desk

   If you come across a bug or get stuck with a certain aspect of ScopeSim or
   the METIS package, please get in touch with us (emails addresses below).

   **Your feedback is the only way we know** what needs to be changed/improved
   with the package and the simulator


Installation & setup
--------------------

``pip install scopesim``

1. Create a directory where your simulation notebooks will live, e.g. ``~/ScopeSim``
2. install relevant irdb packages & download example notebooks into this directory
3. in a Terminal, cd to ~/ScopeSim and execute jupyter notebook METIS_IMG_N.ipynb
4. follow instruction and explanations in the notebook.


Python notebooks
----------------

The example Python (Jupyter) notebooks can be `downloaded from the Github repo
<https://github.com/AstarVienna/irdb/tree/master/METIS/docs/example_notebooks>`_

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   example_notebooks/IMG-HL_Tau


Documentation and useful references
-----------------------------------

- `ScopeSim documentation <https://scopesim.readthedocs.io/en/latest/>`_

- `Sky Object Templates documentation <https://scopesim-templates.readthedocs.io/en/latest/>`_

- `METIS homepage <https://metis.strw.leidenuniv.nl/>`_

- For experts: GitHub repositories:

  - `simulator package ScopeSim <https://github.com/AstarVienna/scopesim>`_
  - `instrument-specific packages irdb <https://github.com/AstarVienna/irdb>`_.




Contact points
--------------

- simmetis.astro@univie.ac.at
- kieran.leschinski@univie.ac.at
