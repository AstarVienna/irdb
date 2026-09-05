## [[sso-etc:Cycle_1|ETC - Cycle 1]]

###  Status of the software ETC

While there are no deliveries expected for ESO, we are configuring the ScopeSim observation simulator for the MOSAIC science team to run feasibility studies for their science cases.

Slide deck with current status (Dec 2025): https://docs.google.com/presentation/d/1ETeuM7kiLp1xcO7O2RYnMYhZ6aWak1xdJuDS0vtABWE/edit?usp=sharing

The first draft of the ETC specifications document for ESO can be found here: https://docs.google.com/document/d/1cWhtF89n1mRFJ9IDOIE9Syhfm56tR6-5YGoQeVHBBD0/edit?usp=sharing

#### Functionalities implemented

We have added a MOSAIC v0.1 package to the ScopeSim "Instrument Reference Database" (IRDB) for use by the science team:
* ReadTheDocs: https://irdb.readthedocs.io/en/latest/MOSAIC/docs/readme.html
* Demo Notebook: https://github.com/AstarVienna/irdb/blob/dev_master/MOSAIC/docs/example_notebooks/MOSAIC_demo.ipynb

Modes currently available in the package:
* VIS - MOS-LR-B+R
* VIS - MOS-HR-B1+B2+R1+R2
* NIR - MOS-LR-J+H
* NIR - MOS-HR-H

The MOSAIC package in ScopeSim makes use of the following optical effect descriptions:
  1. ADConversion
  2. AutoExposure
  3. BasicReadoutNoise
  4. DarkCurrent
  5. DetectorList
  6. ExposureIntegration
  7. ExposureOutput
  8. LinearityCurve
  9. LineSpreadFunction
  10. MetisLMSImageSlicer (repurposed for MOSAIC)
  11. MosaicCollapseSpectralTraces
  12. MosaicSpectralTraceList
  13. QuantumEfficiencyCurve
  14. ReferencePixelBorder
  15. SeeingPSF
  16. ShotNoise
  17. TERCurve

#### Limitations

The mIFU modes will be refined and released with the next update:
* NIR - mIFU-LR-J+H
* NIR - mIFU-HR-H

While the technical implementation is not very taxing, how the mIFU traces data 
will be made available to the "science user" in the context of an "ETC-like" tool
is still under discussion.

###  Version of the software
* ScopeSim for MOSAIC v0.1
* ScopeSim: https://github.com/AstarVienna/ScopeSim
* MOSAIC instrument package: https://github.com/AstarVienna/Irdb/tree/dev_master/MOSAIC

### Development incrementation

#### New features
* Added MOSAIC v0.1 package to the IRDB for use by the science team
* 4 VIS and 2 NIR MOS spectroscopy modes available
* 17 ScopeSim optical effect classes integrated

#### Bug corrections
* No bug corrections to report for this cycle

### functionalities to be implemented in the next cycle
* Refine and release mIFU modes (NIR - mIFU-LR-J+H, NIR - mIFU-HR-H)
* Add a tool to estimate SN-ratios for specfic lines. Currently this is left as
  exercise to the user, however it should be available in a standardised manner.

