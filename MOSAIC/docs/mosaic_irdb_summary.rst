MOSAIC Instrument Package Summary
=================================

This document summarises the current state of the MOSAIC instrument package
in the IRDB, for use in progress reporting.


Observation Modes
-----------------

The MOSAIC package defines **12 observation modes** across three instrument
categories. All modes currently have development status. The default mode is
``MOS-LR-R``.

Visual (VIS) Spectroscopy
+++++++++++++++++++++++++

======== ============= ==================
Mode     Resolution    Dispersion (um/px)
======== ============= ==================
MOS-LR-B R = 32 000    1.9e-5
MOS-LR-R R = 32 000    3.0e-5
MOS-HR-B1 R = 72 000   6.5e-6
MOS-HR-B2 R = 72 000   5.0e-6
MOS-HR-R1 R = 72 000   8.0e-6
MOS-HR-R2 R = 72 000   1.0e-5
======== ============= ==================

NIR Multi-Object Spectroscopy (MOS)
++++++++++++++++++++++++++++++++++++

======== ============= ==================
Mode     Resolution    Dispersion (um/px)
======== ============= ==================
MOS-LR-J R = 16 000    9.5e-5
MOS-LR-H R = 16 000    9.0e-5
MOS-HR-H R = 72 000    2.4e-5
======== ============= ==================

NIR Integral Field Unit (mIFU)
++++++++++++++++++++++++++++++

======== ============= ==================
Mode     Resolution    Dispersion (um/px)
======== ============= ==================
mIFU-LR-J R = 16 000   9.5e-5
mIFU-LR-H R = 16 000   9.0e-5
mIFU-HR-H R = 72 000   2.4e-5
======== ============= ==================


ScopeSim Effect Classes
-----------------------

The MOSAIC package uses **17 unique ScopeSim Effect classes** across its YAML
configuration files.

========================== =======================================
Effect Class               Used In
========================== =======================================
ADConversion               MOSAIC_DET_NIR, MOSAIC_DET_VIS
AutoExposure               MOSAIC_DET_NIR
BasicReadoutNoise          MOSAIC_DET_NIR, MOSAIC_DET_VIS
DarkCurrent                MOSAIC_DET_NIR, MOSAIC_DET_VIS
DetectorList               MOSAIC_DET_NIR, MOSAIC_DET_VIS
ExposureIntegration        MOSAIC_DET_NIR, MOSAIC_DET_VIS
ExposureOutput             MOSAIC_DET_NIR
LinearityCurve             MOSAIC_DET_NIR
LineSpreadFunction         MOSAIC_NIR, MOSAIC_VIS
MetisLMSImageSlicer        MOSAIC_NIR, MOSAIC_VIS
MosaicCollapseSpectralTraces MOSAIC_DET_NIR, MOSAIC_DET_VIS
MosaicSpectralTraceList    MOSAIC_NIR, MOSAIC_VIS
QuantumEfficiencyCurve     MOSAIC_DET_NIR, MOSAIC_DET_VIS
ReferencePixelBorder       MOSAIC_DET_NIR
SeeingPSF                  MOSAIC_NIR, MOSAIC_VIS
ShotNoise                  MOSAIC_DET_NIR, MOSAIC_DET_VIS
TERCurve                   MOSAIC_NIR, MOSAIC_VIS
========================== =======================================

Of these, ``MosaicCollapseSpectralTraces`` and ``MosaicSpectralTraceList`` are
MOSAIC-specific custom effects. ``MetisLMSImageSlicer`` is reused from the
METIS instrument package.


YAML Configuration Files
-------------------------

============================== ==========================================
File                           Purpose
============================== ==========================================
``default.yaml``               Top-level config and mode definitions
``MOSAIC_NIR.yaml``            NIR instrument optical effects
``MOSAIC_VIS.yaml``            VIS instrument optical effects
``MOSAIC_DET_NIR.yaml``        NIR detector (H4RG) effects
``MOSAIC_DET_VIS.yaml``        VIS detector effects
============================== ==========================================
