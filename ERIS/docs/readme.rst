ERIS
====

Introduction
------------

ERIS (Enhanced Resolution Imager and Spectrograph) is a Cassegrain AO instrument
on VLT UT4, replacing NACO and SINFONI. It combines the NIX imager (1-5 um)
with the SPIFFIER IFU spectrograph (1-2.5 um), both fed by a common AO module
using the Adaptive Optics Facility (deformable secondary mirror + laser guide star).

This ScopeSim instrument package provides simulation capabilities for the NIX
imager in all pixel scales and AO modes.

Reference: `Davies et al. 2023, A&A 674, A207 <https://doi.org/10.1051/0004-6361/202346559>`_

Implemented Modes
-----------------

**AO modes** (first axis of mode selection):

- ``NGS`` -- Natural Guide Star AO (Strehl ~80% K-band for bright guide stars)
- ``LGS`` -- Laser Guide Star AO (with off-axis tip-tilt star)
- ``SE`` -- Seeing Enhancer (LGS without tip-tilt star)
- ``NOAO`` -- No AO correction (seeing limited)

**NIX imaging modes** (second axis):

- ``nixIMG_JHK13`` -- JHK bands at 13 mas/pix (26.4" FoV)
- ``nixIMG_JHK27`` -- JHK bands at 27 mas/pix (55.4" FoV)
- ``nixIMG_LM13`` -- LM bands at 13 mas/pix (26.4" FoV)

**Usage example**::

    import scopesim
    cmd = scopesim.UserCommands(
        use_instrument="ERIS",
        properties={
            "!OBS.modes": ["NGS", "nixIMG_JHK13"],
            "!OBS.filter_name": "Ks",
            "!OBS.dit": 60,
        },
    )
    opt = scopesim.OpticalTrain(cmd)

**17 NIX filters available:**
J, H, Ks, Short-Lp, Lp, L-Broad, Mp, Pa-b, Fe-II, H2-cont, H2-1-0S,
Br-g, K-peak, IB-2.42, IB-2.48, Br-a-cont, Br-a.


Validation
----------

Radiometry tests compare ScopeSim output against ESO reference values.
Run with::

    pytest ERIS/tests/ -m slow -v

The test suite generates a radiometry report with throughput curves,
limiting magnitude plots, and star field images in ``ERIS/docs/``.

See `radiometry_report.md <radiometry_report.md>`_ for the latest results.


Package structure
-----------------

::

    ERIS/
    +-- default.yaml                 Master configuration (all mode definitions)
    +-- ERIS.yaml                    Common AO warm optics
    +-- ERIS_AO_NGS/LGS/SE/NOAO.yaml  AO mode PSF configurations
    +-- ERIS_NIX.yaml                NIX filter wheel (17 filters)
    +-- ERIS_NIX_IMG_JHK13.yaml      JHK 13mas/pix mode
    +-- ERIS_NIX_IMG_JHK27.yaml      JHK 27mas/pix mode
    +-- ERIS_NIX_IMG_LM13.yaml       LM 13mas/pix mode
    +-- ERIS_NIX_H2RG.yaml           Detector (slow/fast readout modes)
    +-- filters/                     17 filter curves from SVO
    +-- tests/                       Unit + radiometry tests
    +-- docs/                        Auto-generated reports and plots


Future development
------------------

- **Phase 1c:** NIX special modes (APP, FPC, SAM, LSS)
- **Phase 1d:** AO PSFs from tiptop_ipy (replacing placeholder SeeingPSF)
- **Phase 2:** SPIFFIER IFU spectrograph (32-slice, 12 grating configs)

See ``ERIS/background_info/planning/`` for detailed implementation plans.


Contact
-------

- Kieran Leschinski (kieran.leschinski@univie.ac.at)
