.. |pic1| image:: micado_scopesim_logo.png
   :width: 600px
   :alt: MICADO + ScopeSim

|pic1|
======

Introduction
------------
A new MICADO data simulator is being developed as part of the generic simulator ScopeSim, a descendant of the older SimCADO software.


Prerequisites
-------------

- A working installation of Python 3.6 or newer
- A working installation of Jupyter notebooks if you want to run the simulator from notebooks, i.e. using a graphical interactive interface, rather than just the terminal or scripts (highly recommended)
- A working installation of the Python package installer pip

.. note:: Bug reports and help-desk

   If you come across a bug or get stuck with a certain aspect of ScopeSim or
   the MICADO package, please get in touch with us (emails addresses below).

   **Your feedback is the only way we know** what needs to be changed/improved
   with the package and the simulator


Installation & setup
--------------------

1. Install ``scopesim`` in your python environment::

    $ pip install scopesim

2. Create a directory where your simulation notebooks will live, e.g. ``~/path/to/playing_with_scopesim/``
3. Install relevant irdb packages & download example notebooks into this directory::

    $ python
    >> import scopesim
    >> scopesim.download_packages(["Armazones", "ELT", "MICADO"])

4. Download one of the tutorial notebooks (see `Python notebooks`_)
5. In a Terminal, cd to ~/ScopeSim and execute the notebook by calling::

    $ cd ~/path/to/playing_with_scopesim/
    $ jupyter notebook filename.ipynb

6. Follow instruction and explanations in the notebook.


Python notebooks
----------------

.. note::
   To download a notebook from Github, either:

   - view the raw file and save this disk from the browser, or
   - navigate up one level, then right click the file and save as


**Download the example notebooks** `from the Github repo
<https://github.com/AstarVienna/irdb/tree/master/MICADO/docs/example_notebooks>`_


.. toctree::
   :maxdepth: 1
   :caption: List of notebooks for MICADO

   example_notebooks/1_scopesim_MCAO_4mas_galaxy
   example_notebooks/2_scopesim_SCAO_1.5mas_astrometry
   example_notebooks/3_scopesim_SCAO_4mas_fv-psf
   example_notebooks/MICADO_FAQs


Scientific use-case notebooks
+++++++++++++++++++++++++++++

.. list-table:: Science case notebooks
   :widths: 25 75
   :header-rows: 1

   * - Name
     - Description
   * - <add title>
     - <add description>



Documentation and useful references
-----------------------------------

- `ScopeSim documentation <https://scopesim.readthedocs.io/en/latest/>`_
- `Sky Object Templates documentation <https://scopesim-templates.readthedocs.io/en/latest/>`_
- `MICADO homepage <https://www.mpe.mpg.de/7525659/MICADO>`_
- For experts: GitHub repositories:

  + `simulator package ScopeSim <https://github.com/AstarVienna/scopesim>`_
  + `instrument-specific packages irdb <https://github.com/AstarVienna/irdb>`_.


Contact points
--------------

- kieran.leschinski@univie.ac.at
- oliver.czoske@univie.ac.at
