MAVIS
=====

MAVIS (MCAO Assisted Visible Imager and Spectrograph) is a next-generation
instrument for the VLT UT4 (Yepun) at the Nasmyth A focus, planned for
first light around 2027. MAVIS uses a Multi-Conjugate Adaptive Optics
(MCAO) system to deliver diffraction-limited images in the visible over a
30×30 arcsecond field of view.

AO System
---------

- **Type:** MCAO (Multi-Conjugate AO)
- **Laser Guide Stars:** Up to 5 LGS on a 17.5" ring
- **Deformable Mirrors:** 3 DMs
- **Natural Guide Stars:** Up to 3 NGS for tip-tilt
- **Wavelength correction range:** 370–1000 nm
- **Strehl at 550 nm:** >8% (goal 12%)
- **Ensquared energy:** >15% within 50 mas at 550 nm

Imager Parameters
-----------------

+---------------------------+------------------------------------+
| Parameter                 | Value                              |
+===========================+====================================+
| Pixel scale               | 7.36 mas/pixel                     |
+---------------------------+------------------------------------+
| Field of view             | 30" × 30"                          |
+---------------------------+------------------------------------+
| Detector                  | Back-illuminated CCD, 4096×4004    |
+---------------------------+------------------------------------+
| Pixel pitch               | 10 µm                              |
+---------------------------+------------------------------------+
| Wavelength range          | 370–1000 nm                        |
+---------------------------+------------------------------------+
| Read noise (slow mode)    | 3 e⁻                               |
+---------------------------+------------------------------------+
| Read noise (fast mode)    | 5 e⁻                               |
+---------------------------+------------------------------------+
| Full well capacity        | 90,000 e⁻                          |
+---------------------------+------------------------------------+
| Gain                      | 1.0 ADU/e⁻                         |
+---------------------------+------------------------------------+
| QE at 550 nm              | 89%                                |
+---------------------------+------------------------------------+
| AO module throughput      | ~63% at 550 nm                     |
+---------------------------+------------------------------------+
| PSF FWHM (design, 550 nm) | ~10 mas                            |
+---------------------------+------------------------------------+
| Sky background (V-band)   | 21.61 mag/arcsec²                  |
+---------------------------+------------------------------------+

Available Filters
-----------------

Broadband (Bessel/Cousins):

- **B** – Bessel B (~390–510 nm)
- **V** – Bessel V (centre 550 nm, FWHM 88 nm)
- **R** – Cousins R (~580–730 nm)
- **I** – Cousins I (~730–910 nm)

Broadband (SDSS):

- **u** – SDSS u' (~315–395 nm)
- **g** – SDSS g' (~400–555 nm)
- **r_SDSS** – SDSS r' (~560–705 nm)
- **i_SDSS** – SDSS i' (~690–835 nm)
- **z** – SDSS z' (~835–1000 nm, limited by CCD QE)

.. note::
   SDSS r and i are named ``r_SDSS`` and ``i_SDSS`` (not ``r``/``i``) to avoid
   filesystem case-collision with Cousins R and I on case-insensitive systems.

.. note::
   Filter curves are **approximate top-hat profiles**. Replace with
   measured transmission curves from ESO or the SVO Filter Profile Service
   for science-grade simulations.

PSF Placeholder
---------------

The packaged PSF file ``PSF_MAVIS_placeholder.fits`` contains a simple
Gaussian PSF at 5 wavelengths (400–1000 nm) with FWHM values representative
of the MAVIS AO design goal (10 mas at 550 nm). This is a placeholder only.

For science-grade simulations:

1. Generate realistic MCAO PSFs using `MAVISIM <https://github.com/smonty93/mavisim>`_
   (Monty et al. 2021, MNRAS 507:2192).
2. Replace ``PSF_MAVIS_placeholder.fits`` with the output FITS file from MAVISIM.
3. Update ``MAVIS_IMG.yaml`` to point to the real PSF file.

Known Limitations
-----------------

- Filter curves are approximate (top-hat). Measured curves preferred.
- QE curve is approximate; manufacturer data preferred.
- AO module throughput is a flat approximation based on 550 nm nominal value.
  Wavelength-resolved curve from the MAVIS consortium preferred.
- Dark current is estimated (0.001 e⁻/s); real characterisation needed.
- IFU spectrograph modes are not yet implemented.

References
----------

- Monty et al. 2021, MNRAS 507:2192 – MAVISIM paper
- MAVIS Science Case: https://arxiv.org/abs/2009.09242
- MAVIS project website: https://mavis-ao.org/mavis/
- MAVISIM GitHub: https://github.com/smonty93/mavisim
