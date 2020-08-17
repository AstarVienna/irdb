# MICADO Science package

## What effects are needed

### General
* Telescope system TER  [MICADO.yaml:TEL]
* AtmosphericTERCurve   [MICADO.yaml:ATMO]
* FilterCurve           [MICADO.yaml:INST]
* MICADO common optics  **
* QE curve              [MICADO_detector.yaml:DET]
* RON                   [MICADO_detector.yaml:DET]
* Dark                  [MICADO_detector.yaml:DET]
* average stack         **
* Shot_noise            [MICADO_detector.yaml:DET]

#### SCAO
* RO TER
* Detector Window       [MICADO_detector.yaml:DET, (w,h) in MICADO_SCAO.yaml:DET]
* PSF                   **
    * SCAO FVPSF 
    * SCAO AnisoCADO ConstPSF  

#### MCAO
* MAORY TER
* Detector Window
* PSF
    * MCAO StrehlPSF (max SR JHK-13/30/50)


### SPEC
* RO TER
* SPEC TER
* SkyCalcTERCurve
* Detector Window

* ApertureMask
    * filename_format
    * mask_name

* XiLamConverter
* XiLamStrehlPSF (max SR JHK-40/60/80)
* BasicTraceMap
* AtmopshericDiffraction
