# MICADO Science package

## What effects are needed

### General
* SkycalcTERCurve       [MICADO_Sci.yaml:ATMO]
* Telescope system TER  [MICADO_Sci.yaml:TEL]
* FilterCurve           [MICADO_Sci.yaml:INST]
* MICADO common optics  [MICADO_Sci.yaml:INST]
* QE curve              [MICADO_Sci_detector.yaml:DET]
* RON                   [MICADO_Sci_detector.yaml:DET]
* Dark                  [MICADO_Sci_detector.yaml:DET]
* average stack         **
* Shot_noise            [MICADO_Sci_detector.yaml:DET]

#### SCAO
* RO TER                [MICADO_Sci_SCAO.yaml:INST]
* Detector Window       [MICADO_sci_detector.yaml:DET, (w,h) in MICADO_Sci_SCAO.yaml:DET]
* PSF                   
    * SCAO FVPSF                **
    * SCAO AnisoCADO ConstPSF   [MICADO_Sci_SCAO.yaml:INST]  

#### MCAO
* MORFEO TER             [MICADO_Sci_MCAO.yaml:INST]
* Detector Window       [MICADO_sci_detector.yaml:DET, (w,h) in MICADO_Sci_MCAO.yaml:DET]
* PSF
    * MCAO StrehlPSF (max SR JHK-13/30/50)  [MICADO_Sci_SCAO.yaml:INST]


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
