"""Generate MAVIS/PSF_MAVIS_analytic.fits — an analytic MCAO PSF for the imager.

MAVIS is not built, and the consortium end-to-end PSF products (LAM, MAVISIM)
are hundreds of MB and not redistributable here. This script builds a
self-contained analytic stand-in that is *derived* rather than drawn: it uses
the true VLT pupil geometry and is fitted to the two published MAVIS
performance requirements.

Model
-----
Three radial components, each normalised to unit total energy::

    PSF(theta, lam) = a(lam) * Airy(theta, lam)          # diffraction core
                    + b(lam) * Moffat(theta, w_corr)     # AO-corrected halo
                    + c(lam) * Moffat(theta, w_seeing)   # uncorrected seeing halo

* ``Airy`` is the *obscured* Airy pattern for the VLT UT4 pupil,
  D = 8.2 m with a 1.0 m central obstruction, matching
  ``VLT/LIST_VLT_mirrors.dat`` so that the PSF and the collecting area used for
  photometry describe the same telescope.
* ``w_corr = K_CORR * lambda / D`` is the residual halo left by a finite number
  of corrected modes.
* ``w_seeing`` is the natural seeing FWHM, scaled as ``lambda ** (-1/5)``
  (von Karman / Kolmogorov).
* ``a + b + c = 1`` at every wavelength.

Calibration
-----------
At 550 nm the two free amplitudes are solved so the PSF reproduces both
published numbers simultaneously (see
``mavis_baseline_specification.md``)::

    Strehl ratio            = STREHL_550   (spec: > 8 %, goal 12 %)
    Ensquared energy in a
    50 mas box              = EE50_550     (spec: > 15 %)

``K_CORR`` is not constrained by those two numbers and is fixed at a
conventional value; it sets how compact the partially-corrected halo is.

At other wavelengths the core amplitude follows the Marechal approximation,
``S(lam) = exp(-(2 pi sigma / lam) ** 2)``, with ``sigma`` the residual
wavefront error implied by the 550 nm Strehl. The split of the remaining
energy between corrected halo and seeing halo is held at its 550 nm ratio.

This is a *model*, not a simulation. It gets the core width, the diffraction
rings, the halo, the Strehl and the ensquared energy right, which is what
matters for photometry and for point-source sensitivity. It does not
reproduce field variability, PSF elongation towards the field edge, or the
anisoplanatic structure that a real MCAO PSF shows. For that, use MAVISIM.

Run from the repository root::

    python MAVIS/background_info/make_psf.py
"""

from datetime import date
from pathlib import Path

import numpy as np
from astropy.io import fits

from scipy.special import j1

# --- telescope, from VLT/LIST_VLT_mirrors.dat ------------------------------
D_TEL = 8.2          # [m] M1 outer diameter
D_OBS = 1.0          # [m] M1 central obstruction

# --- published MAVIS performance, at 550 nm --------------------------------
STREHL_550 = 0.10    # spec > 8 %, goal 12 %; midpoint used here
EE50_550 = 0.15      # spec: > 15 % ensquared energy within 50 mas
EE_BOX = 0.050       # [arcsec] the box the EE spec refers to

# --- model parameters ------------------------------------------------------
K_CORR = 6.0         # AO-corrected halo width, in units of lambda / D
SEEING = 0.8         # [arcsec] natural seeing at 500 nm, matches default.yaml
SEEING_REF = 0.5     # [um] wavelength the seeing value refers to
MOFFAT_BETA = 2.5    # Moffat index for both halo components

# --- output grid -----------------------------------------------------------
WAVELENGTHS = [0.40, 0.55, 0.70, 0.85, 1.00]   # [um]
PIX_SCALE = 0.00368   # [arcsec/pix] half the 7.36 mas detector pixel
N_PIX = 501           # -> +/- 0.92 arcsec, enough to carry the seeing halo

OUT_PATH = Path(__file__).resolve().parent.parent / "PSF_MAVIS_analytic.fits"

ARCSEC = np.pi / (180.0 * 3600.0)


def airy_obscured(theta_arcsec, lam_um):
    """Obscured Airy intensity, peak-normalised to 1.0."""
    eps = D_OBS / D_TEL
    lam_m = lam_um * 1e-6
    x = np.pi * D_TEL * (theta_arcsec * ARCSEC) / lam_m
    x = np.where(x == 0.0, 1e-12, x)

    term = (2 * j1(x) / x - eps * 2 * j1(eps * x) / (eps * x)) / (1 - eps ** 2)
    return term ** 2


def moffat(theta_arcsec, fwhm_arcsec, beta=MOFFAT_BETA):
    """Moffat intensity, peak-normalised to 1.0."""
    alpha = fwhm_arcsec / (2 * np.sqrt(2 ** (1 / beta) - 1))
    return (1 + (theta_arcsec / alpha) ** 2) ** (-beta)


def unit_energy(profile):
    """Scale a 2D profile so its pixels sum to unit energy."""
    return profile / profile.sum()


def build_components(lam_um, theta):
    """Return the three unit-energy components at one wavelength."""
    core = unit_energy(airy_obscured(theta, lam_um))

    lam_over_d = (lam_um * 1e-6 / D_TEL) / ARCSEC       # [arcsec]
    corr = unit_energy(moffat(theta, K_CORR * lam_over_d))

    seeing_lam = SEEING * (lam_um / SEEING_REF) ** (-0.2)
    halo = unit_energy(moffat(theta, seeing_lam))

    return core, corr, halo


def ensquared(image, pix_scale, box_arcsec):
    """Energy inside a centred square box, for a unit-total-energy image."""
    n = image.shape[0]
    c = n // 2
    half = int(round(0.5 * box_arcsec / pix_scale))
    return image[c - half:c + half + 1, c - half:c + half + 1].sum()


def calibrate(theta, pix_scale):
    """Solve the 550 nm amplitudes against the Strehl and EE requirements.

    Both constraints are linear in the amplitudes, so this is a 2x2 solve
    rather than a search. With ``c = 1 - a - b``:

        a (P_core - P_halo) + b (P_corr - P_halo) = S * P_core - P_halo
        a (E_core - E_halo) + b (E_corr - E_halo) = EE       - E_halo

    where ``P_*`` are the component peak values and ``E_*`` their ensquared
    energies in the spec box.

    Returns (a550, b550, c550, sigma_nm).
    """
    core, corr, halo = build_components(0.55, theta)

    peaks = np.array([core.max(), corr.max(), halo.max()])
    ees = np.array([ensquared(comp, pix_scale, EE_BOX)
                    for comp in (core, corr, halo)])

    matrix = np.array([[peaks[0] - peaks[2], peaks[1] - peaks[2]],
                       [ees[0] - ees[2], ees[1] - ees[2]]])
    rhs = np.array([STREHL_550 * peaks[0] - peaks[2],
                    EE50_550 - ees[2]])

    a, b = np.linalg.solve(matrix, rhs)
    c = 1.0 - a - b

    if min(a, b, c) < 0:
        raise ValueError(
            f"unphysical calibration: a={a:.4f} b={b:.4f} c={c:.4f}. "
            "The Strehl and ensquared-energy targets cannot both be met with "
            "this K_CORR / seeing combination."
        )

    # Residual wavefront error implied by the *Strehl* target, via Marechal.
    sigma_nm = 550.0 * np.sqrt(-np.log(STREHL_550)) / (2 * np.pi)
    return float(a), float(b), float(c), float(sigma_nm)


def core_fraction(strehl, core, corr, halo, halo_split):
    """Core amplitude that yields ``strehl``, at fixed corrected/seeing ratio.

    The non-core energy ``1 - a`` is divided between the corrected halo and
    the seeing halo in the ratio fixed at 550 nm, so the Strehl constraint
    alone determines ``a``.
    """
    q = halo_split * corr.max() + (1 - halo_split) * halo.max()
    return (strehl * core.max() - q) / (core.max() - q)


def main():
    half = (N_PIX - 1) // 2
    axis = (np.arange(N_PIX) - half) * PIX_SCALE
    xx, yy = np.meshgrid(axis, axis)
    theta = np.hypot(xx, yy)

    a550, b550, c550, sigma_nm = calibrate(theta, PIX_SCALE)
    halo_split = b550 / (b550 + c550)

    print(f"calibration at 550 nm: core={a550:.4f} corr_halo={b550:.4f} "
          f"seeing_halo={c550:.4f}")
    print(f"implied residual wavefront error: {sigma_nm:.1f} nm RMS")

    primary = fits.PrimaryHDU()
    primary.header["INSTRUME"] = "MAVIS"
    primary.header["PSF_TYPE"] = ("analytic", "not an end-to-end simulation")
    primary.header["D_TEL"] = (D_TEL, "[m] VLT M1 outer diameter")
    primary.header["D_OBS"] = (D_OBS, "[m] central obstruction")
    primary.header["SEEING"] = (SEEING, "[arcsec] natural seeing at 500 nm")
    primary.header["WFE_RMS"] = (round(float(sigma_nm), 1),
                                 "[nm] residual wavefront error")
    primary.header["K_CORR"] = (K_CORR, "corrected halo width in lambda/D")
    primary.header["DATE"] = date.today().isoformat()
    for line in (
        "Analytic MCAO PSF: obscured Airy core + corrected halo + seeing halo.",
        f"Fitted at 550 nm to Strehl={STREHL_550} and ensquared energy",
        f"{EE50_550} within a {EE_BOX * 1000:.0f} mas box, per the ESO MAVIS",
        "baseline. Wavelength dependence of the core follows Marechal.",
        "Not a substitute for MAVISIM: no field variability or anisoplanatism.",
        "Generated by MAVIS/background_info/make_psf.py",
    ):
        primary.header["COMMENT"] = line

    hdus = [primary]
    print(f"{'lam[um]':>8s} {'Strehl':>8s} {'EE50mas':>8s} {'FWHM[mas]':>10s}")
    for lam in WAVELENGTHS:
        core, corr, halo = build_components(lam, theta)

        strehl_target = float(
            np.exp(-(2 * np.pi * sigma_nm / (lam * 1000.0)) ** 2))

        # How much of the non-core light sits in the AO-corrected halo rather
        # than in the raw seeing halo. This has to fall towards the blue,
        # where the loop corrects a smaller fraction of the turbulence, so it
        # is scaled with the Strehl relative to the 550 nm calibration point.
        split = float(np.clip(halo_split * strehl_target / STREHL_550,
                              0.0, 1.0))

        a = core_fraction(strehl_target, core, corr, halo, split)
        a = float(np.clip(a, 0.0, 1.0))
        rest = 1.0 - a
        b = rest * split
        c = rest - b

        psf = a * core + b * corr + c * halo
        psf = psf / psf.sum()                      # unit total energy

        perfect = core / core.sum()
        strehl = psf.max() / perfect.max()
        ee50 = ensquared(psf, PIX_SCALE, EE_BOX)

        # FWHM of the core, measured on the radial profile
        prof = psf[half, :]
        above = np.where(prof >= 0.5 * prof.max())[0]
        fwhm_mas = (above[-1] - above[0] + 1) * PIX_SCALE * 1000.0

        print(f"{lam:8.2f} {strehl:8.3f} {ee50:8.3f} {fwhm_mas:10.1f}")

        hdu = fits.ImageHDU(psf.astype(np.float32))
        hdu.header["WAVE0"] = (lam, "[um] wavelength of this PSF plane")
        hdu.header["CDELT1"] = PIX_SCALE
        hdu.header["CDELT2"] = PIX_SCALE
        hdu.header["CUNIT1"] = "arcsec"
        hdu.header["CUNIT2"] = "arcsec"
        hdu.header["CRPIX1"] = half + 1
        hdu.header["CRPIX2"] = half + 1
        hdu.header["CRVAL1"] = 0.0
        hdu.header["CRVAL2"] = 0.0
        hdu.header["STREHL"] = (round(float(strehl), 4), "modelled Strehl ratio")
        hdu.header["EE50MAS"] = (round(float(ee50), 4),
                                 "ensquared energy in a 50 mas box")
        hdus.append(hdu)

    fits.HDUList(hdus).writeto(OUT_PATH, overwrite=True)
    size_mb = OUT_PATH.stat().st_size / 1024 ** 2
    print(f"wrote {OUT_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
