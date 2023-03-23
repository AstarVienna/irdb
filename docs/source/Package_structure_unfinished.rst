File structure of a package
===========================
A package should contain the following files:

default.yaml
------------
The following yaml keys should be include at the beginning of this file:

    object : observation
    alias : OBS
    name :
    description :

Plus any other meta data that you deem necessary

Next it should contain a list of the packages needed for a simulation to run.
These entries refer to the name of the folder where these extra packages are
kept, and should all be found inside the directory specified by the ScopeSim
RC parameter ``scopesim.__rc__["!SIM.file.local_packages_path"]``::

    packages :
    - Armazones
    - ELT
    - MORFEO
    - MICADO

Next a list of the yaml files containing the default setup for the optical
system should be included. These file names refer to yaml files found in any
one of the packages listed above::

    yamls :
    - Armazones.yaml
    - ELT.yaml
    - MORFEO.yaml
    - MICADO.yaml
    - MODE_IMG_wide.yaml
    - H4RG.yaml

With these two lists ScopeSim has enough information to build the basic optical
system.

Next is the ``properties`` list which corresponds to any !OBS. keywords.


<OpticalElement>.yaml
---------------------



<DataFile>.yaml
---------------


