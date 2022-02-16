.. |pic1| image:: metis_scopesim_logo.png
   :width: 600px
   :alt: METIS + ScopeSim

|pic1|
======

Introduction
------------
For the preparation of FDR documentation, a new METIS data simulator is being developed that is technically an instrument-package for the generic simulator ScopeSim, a descendant of the older SimCado/SimMETIS interface.
The new METIS data simulator currently supports the imaging and long-slit modes and the LM-band high-resolution IFU (LMS) mode is planned to be offered soon, too.
The old data simulator, `SimMETIS v0.3 <https://metis.strw.leidenuniv.nl/simmetis/>`_, can still be used for simulating LMS observations.


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
3. in a Terminal, cd to ~/ScopeSim and execute the notebook by calling ``jupyter notebook filename.ipynb``
4. follow instruction and explanations in the notebook.


Python notebooks
----------------

Download the example notebooks `from the Github repo
<https://github.com/AstarVienna/irdb/tree/master/METIS/docs/example_notebooks>`_

Input image and cube files for the notebooks can be `found on our google drive
<https://drive.google.com/drive/folders/1Lqux93ymgMM_ZXSSUUPMBnow5sgbo-bb?usp=sharing>`_

.. note::
   To download a notebook from Github, either:
   
   - view the raw file and save this disk from the browser, or
   - navigate up one level, then right click the file and save as


.. list-table:: Python Notebooks
   :widths: 25 25 25 25
   :header-rows: 1

   * - Name
     - Description
     - Download Link
     - Required Data Files
   * - Imaging with HL Tau
     - <add description>
     - `Notebook Link <https://raw.githubusercontent.com/AstarVienna/irdb/master/METIS/docs/example_notebooks/IMG-HL_Tau.ipynb>`_
     - `HL Tau FITS image <https://drive.google.com/file/d/1LmKUw8wZkpTw2ZSAOn2ykui0q2RGZ2sA/view?usp=sharing>`_
   * - <add title>
     - <add description>
     - <add notebook link>
     - <add data files links>


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

  + `simulator package ScopeSim <https://github.com/AstarVienna/scopesim>`_
  + `instrument-specific packages irdb <https://github.com/AstarVienna/irdb>`_.


Contact points
--------------

.. list-table:: Python Notebooks
   :widths: 33 33 33
   :header-rows: 1
* - simmetis.astro@univie.ac.at
  - oliver.czoske@univie.ac.at
  - kieran.leschinski@univie.ac.at
