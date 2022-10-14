MOSAIC package
==============

Created: 2022-10-13
Author: Kieran Leschinski

Basic Information
-----------------
GLAO
FOV = 7.5"
2x spectrographs: Vis, NIR
1x Vis Detector, 3x NIR detectors (H4RGs)

Wavelength ranges:
    RI: (0.770, 1.045)
    YJ: (1.010, 1.370)
    H:  (1.420, 1.925)
Spectral resolution:
    LR: R=4000
    HR: R=20000

Small aperture bundles:
    7 fibres
    0.7" or 0.233" per fibre
Large aperture bundles:
    19 fibres
    Vis: 0.7" or 0.14" per fibre
    NIR: 0.6" or 0.12" per fibre
IFU bundles:
    441 fibres: (15*21 + 2*18 + 2*15 + 2*12 + 2*9 + 2*6 + 2*3)
    2.5" or 0.150" per fibre

Vis_LR  = 200 SAB
Vis_HR  = 100 LAB
NIR     = 200 LAB
IFU     = 8 IFU bundles -> 3528 Traces


Derived information
-------------------
Easiest scenario: Vis_LR
    200 * 7 fibres on 1 4k detector:
    1400 trace images of length (4096, 1)

Trickiest scenario: IFU
    441 * 8 bundles on 3 4k detectors (3 * 3528)
    10584 trace images of length (4096, 1)
