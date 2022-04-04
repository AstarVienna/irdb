# ScopeSim's Instrument reference database

[![Documentation Status](https://readthedocs.org/projects/scopesim-templates/badge/?version=latest)](https://scopesim-templates.readthedocs.io/en/latest/?badge=latest)
[![Tests](https://github.com/AstarVienna/irdb/actions/workflows/tests.yml/badge.svg)](https://github.com/AstarVienna/irdb/actions/workflows/tests.yml)

[![Python Version Support](http://github-actions.40ants.com/AstarVienna/irdb/matrix.svg)](https://github.com/AstarVienna/irdb)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

This repository contains the data files needed by ``ScopeSim`` to create a model of
any given optical train.

The data is split in the following way:

* Primary observing packages

  e.g. Instruments

  Primary packages are complete packages which can be used by ``scopesim`` to 
  simulate the readout files from a full optical system 
  (i.e. atmosphere + telescope + relay optics + instrument + detector)  

  These packages contain all information regarding the internal working of the 
  instrument, such as optics, detectors, properties (e.g. temperature), etc 

* Support packages

  e.g: Telescopes / Observing sites / Relay optics

  These packages only contain information pertaining to the effects generated 
  by the specific set of optics contained within the optical subsystem. 
  These packages are used to support the Primary packages, and can be shared
  between multiple primary instrument package. 
  
  For example, the ELT package cannot be used to generate images on its own, 
  however it is need by both the MICADO and METIS instument packages.

* PSFs

  Currently PSFs are kept separately, simply due to their size

## Packages kept here

* Armazones
* ELT
* MAORY
* MICADO
* METIS (under construction)

## Status of packages

Detailed information on the test suite can be found in the 

[badge reports section](_REPORTS/badges.md)

