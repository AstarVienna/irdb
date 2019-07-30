# ScopeSim's Instrument reference database

[![Build Status](https://travis-ci.org/astronomyk/irdb.svg?branch=master)](https://travis-ci.org/astronomyk/irdb)

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

Combined status of all packages hosted here, tested by TravisCI:

[![Build Status](https://travis-ci.org/astronomyk/irdb.svg?branch=master)](https://travis-ci.org/astronomyk/irdb)

Detailed information on the test suite can be found in the 
[badge reports section](_REPORTS/badges.md)

