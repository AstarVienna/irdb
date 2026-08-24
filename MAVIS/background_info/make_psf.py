"""Generate MAVIS/PSF_MAVIS_mcao.fits — the MCAO PSF for the MAVIS imager.

The V-band (550 nm) plane is *not* a model: it is the on-axis end-to-end
MCAO PSF from MAVISIM (Monty et al. 2021, MNRAS 507, 2192), produced by the
consortium's LQG tomography simulations (J. Cranney, ANU). Using the same
kernel that MAVISIM convolves with guarantees that ScopeSim and MAVISIM
produce matching V-band images; MAVISIM v1.1 is monochromatic V-band, so
550 nm is the only wavelength where a reference exists.

The other wavelength planes are analytic, calibrated *to that e2e PSF*
rather than to the published performance floor:

    PSF(theta, lam) = a(lam) * Airy(theta, lam)          # diffraction core
                    + b(lam) * Moffat(theta, w_corr)     # AO-corrected halo
                    + c(lam) * Moffat(theta, w_seeing)   # uncorrected seeing halo

* ``Airy`` is the *obscured* Airy pattern for the VLT UT4 pupil,
  D = 8.2 m with a 1.0 m central obstruction, matching
  ``VLT/LIST_VLT_mirrors.dat``.
* At 550 nm the Strehl ratio and the ensquared energy in a 50 mas box are
  *measured from the e2e PSF* and the amplitudes solved to reproduce both
  (2x2 linear solve, see ``calibrate``).
* The residual wavefront error follows from the measured 550 nm Strehl via
  the Marechal approximation and sets the Strehl at the other wavelengths.
* The split of non-core energy between corrected and seeing halo follows
  the Strehl, as in the previous release.

All planes share the same angular window (the e2e PSF's 5.1 arcsec) and the
same 3.75 mas sampling, so the window normalisation — and with it aperture
photometry — is consistent across filters.

The e2e reference file ships with the MAVISIM repository
(``tests/test_psf_e2e.fits``, header: "LQG MAVIS with superres"); the full
field-varying product (1.7 GB, 11x11 grid) is at
https://www.mso.anu.edu.au/~jcranney/mavisim_data/v1_1.tar.gz — this script
only needs the on-axis PSF.

Run from the repository root::

    python MAVIS/background_info/make_psf.py [path/to/test_psf_e2e.fits]
"""

import sys
from datetime import date
from pathlib import Path

import numpy as np
from astropy.io import fits

from scipy.special import j1

# --- telescope, from VLT/LIST_VLT_mirrors.dat ------------------------------
D_TEL = 8.2          # [m] M1 outer diameter
D_OBS = 1.0          # [m] M1 central obstruction

# --- the MAVISIM end-to-end reference PSF -----------------------------------
E2E_DEFAULT = Path("D:/Repos/MAVISIM/tests/test_psf_e2e.fits")
EE_BOX = 0.050       # [arcsec] box for the ensquared-energy calibration

# --- model parameters for the non-V planes ----------------------------------
# K_CORR = 2.0 is the narrowest corrected halo for which the measured 550 nm
# Strehl and ensquared energy can be met with non-negative amplitudes; wider
# halos push the corrected-halo amplitude above 1. It also minimises the rms
# deviation of the model's ensquared-energy curve from the e2e PSF.
K_CORR = 2.0         # AO-corrected halo width, in units of lambda / D
SEEING = 0.8         # [arcsec] natural seeing at 500 nm, matches default.yaml
SEEING_REF = 0.5     # [um] wavelength the seeing value refers to
MOFFAT_BETA = 2.5    # Moffat index for both halo components

# --- output grid (matches the e2e PSF after centring) ------------------------
WAVELENGTHS = [0.40, 0.55, 0.70, 0.85, 1.00]   # [um]
PIX_SCALE = 0.00375   # [arcsec/pix] the MAVISIM e2e sampling
N_PIX = 1361          # odd; e2e is 1362 with its centre at pixel (681, 681)

OUT_PATH = Path(__file__).resolve().parent.parent / "PSF_MAVIS_mcao.fits"

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


def load_e2e(path):
    """Load and centre the MAVISIM e2e PSF.

    MAVISIM stores PSFs on an even grid with the centre of gravity half a
    pixel up-right of the array midpoint (their (0, 0) convention is the
    corner between the middle four pixels). Dropping the first row and
    column gives an odd grid whose central pixel carries the PSF centre.
    """
    with fits.open(path) as hdul:
        hdu = hdul[1]
        if abs(hdu.header["LAMBDA"] - 0.55) > 0.01:
            raise ValueError(
                f"e2e PSF is at {hdu.header['LAMBDA']} um, expected 0.55")
        if abs(hdu.header["PIXSIZE"] - PIX_SCALE) > 1e-6:
            raise ValueError(
                f"e2e PSF sampling {hdu.header['PIXSIZE']} != {PIX_SCALE}")
        data = hdu.data.astype(np.float64)

    data = data[1:, 1:]
    if data.shape != (N_PIX, N_PIX):
        raise ValueError(f"unexpected e2e shape {data.shape}")
    data[data < 0] = 0.0
    return unit_energy(data)


def diffraction_peak(theta_grid_shape, pix_scale):
    """Peak of the unit-energy diffraction-limited PSF on the same grid.

    Computed by FFT of the annular pupil so that the peak is exact for the
    given sampling (an undersampled analytic Airy underestimates it).
    """
    n_fft = 4096
    pix_rad = pix_scale * ARCSEC
    lam_m = 0.55e-6
    dx = lam_m / (n_fft * pix_rad)
    axis = (np.arange(n_fft) - n_fft // 2) * dx
    xx, yy = np.meshgrid(axis, axis)
    rr = np.hypot(xx, yy)
    pupil = ((rr <= D_TEL / 2) & (rr >= D_OBS / 2)).astype(float)
    psf = np.abs(np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(pupil)))) ** 2
    return psf.max() / psf.sum()


def calibrate(theta, pix_scale, strehl_550, ee50_550):
    """Solve the 550 nm amplitudes against the *measured* Strehl and EE.

    Both constraints are linear in the amplitudes, so this is a 2x2 solve.
    With ``c = 1 - a - b``:

        a (P_core - P_halo) + b (P_corr - P_halo) = S * P_core - P_halo
        a (E_core - E_halo) + b (E_corr - E_halo) = EE       - E_halo

    Returns (a550, b550, c550, sigma_nm).
    """
    core, corr, halo = build_components(0.55, theta)

    peaks = np.array([core.max(), corr.max(), halo.max()])
    ees = np.array([ensquared(comp, pix_scale, EE_BOX)
                    for comp in (core, corr, halo)])

    matrix = np.array([[peaks[0] - peaks[2], peaks[1] - peaks[2]],
                       [ees[0] - ees[2], ees[1] - ees[2]]])
    rhs = np.array([strehl_550 * peaks[0] - peaks[2],
                    ee50_550 - ees[2]])

    a, b = np.linalg.solve(matrix, rhs)
    c = 1.0 - a - b

    if min(a, b, c) < 0:
        raise ValueError(
            f"unphysical calibration: a={a:.4f} b={b:.4f} c={c:.4f}. "
            "The Strehl and ensquared-energy targets cannot both be met with "
            "this K_CORR / seeing combination."
        )

    # Residual wavefront error implied by the *Strehl* target, via Marechal.
    sigma_nm = 550.0 * np.sqrt(-np.log(strehl_550)) / (2 * np.pi)
    return float(a), float(b), float(c), float(sigma_nm)


def core_fraction(strehl, core, corr, halo, halo_split):
    """Core amplitude that yields ``strehl``, at fixed corrected/seeing ratio.

    The non-core energy ``1 - a`` is divided between the corrected halo and
    the seeing halo in the ratio fixed at 550 nm, so the Strehl constraint
    alone determines ``a``.
    """
    q = halo_split * corr.max() + (1 - halo_split) * halo.max()
    return (strehl * core.max() - q) / (core.max() - q)


def plane_header(hdu, lam, half, strehl, ee50):
    hdu.header["WAVE0"] = (lam, "[um] wavelength of this PSF plane")
    hdu.header["CDELT1"] = PIX_SCALE
    hdu.header["CDELT2"] = PIX_SCALE
    hdu.header["CUNIT1"] = "arcsec"
    hdu.header["CUNIT2"] = "arcsec"
    hdu.header["CRPIX1"] = half + 1
    hdu.header["CRPIX2"] = half + 1
    hdu.header["CRVAL1"] = 0.0
    hdu.header["CRVAL2"] = 0.0
    hdu.header["STREHL"] = (round(float(strehl), 4), "Strehl ratio")
    hdu.header["EE50MAS"] = (round(float(ee50), 4),
                             "ensquared energy in a 50 mas box")


def main():
    e2e_path = Path(sys.argv[1]) if len(sys.argv) > 1 else E2E_DEFAULT
    e2e = load_e2e(e2e_path)

    half = (N_PIX - 1) // 2
    axis = (np.arange(N_PIX) - half) * PIX_SCALE
    xx, yy = np.meshgrid(axis, axis)
    theta = np.hypot(xx, yy)

    # measure the calibration targets from the e2e PSF
    strehl_550 = float(e2e.max() / diffraction_peak(e2e.shape, PIX_SCALE))
    ee50_550 = float(ensquared(e2e, PIX_SCALE, EE_BOX))
    print(f"measured from MAVISIM e2e PSF: Strehl(550nm)={strehl_550:.4f} "
          f"EE(50mas)={ee50_550:.4f}")

    a550, b550, c550, sigma_nm = calibrate(theta, PIX_SCALE,
                                           strehl_550, ee50_550)
    halo_split = b550 / (b550 + c550)

    print(f"calibration at 550 nm: core={a550:.4f} corr_halo={b550:.4f} "
          f"seeing_halo={c550:.4f}")
    print(f"implied residual wavefront error: {sigma_nm:.1f} nm RMS")

    primary = fits.PrimaryHDU()
    primary.header["INSTRUME"] = "MAVIS"
    primary.header["PSF_TYPE"] = ("hybrid",
                                  "550nm: MAVISIM e2e; other: analytic")
    primary.header["D_TEL"] = (D_TEL, "[m] VLT M1 outer diameter")
    primary.header["D_OBS"] = (D_OBS, "[m] central obstruction")
    primary.header["SEEING"] = (SEEING, "[arcsec] natural seeing at 500 nm")
    primary.header["WFE_RMS"] = (round(float(sigma_nm), 1),
                                 "[nm] residual wavefront error")
    primary.header["K_CORR"] = (K_CORR, "corrected halo width in lambda/D")
    primary.header["E2EFILE"] = (e2e_path.name, "MAVISIM e2e reference PSF")
    primary.header["DATE"] = date.today().isoformat()
    for line in (
        "MAVIS MCAO PSF. The 550 nm plane is the on-axis end-to-end MCAO",
        "PSF from MAVISIM (Monty et al. 2021, MNRAS 507, 2192; LQG",
        "tomography simulations by J. Cranney, ANU). The other planes are",
        "an analytic model (obscured Airy core + corrected halo + seeing",
        "halo) calibrated to the measured 550 nm Strehl and ensquared",
        "energy, with Marechal wavelength scaling of the core.",
        "No field variability or anisoplanatism is included.",
        "Generated by MAVIS/background_info/make_psf.py",
    ):
        primary.header["COMMENT"] = line

    hdus = [primary]
    print(f"{'lam[um]':>8s} {'Strehl':>8s} {'EE50mas':>8s} {'FWHM[mas]':>10s}"
          f" {'origin':>10s}")
    for lam in WAVELENGTHS:
        if lam == 0.55:
            psf = e2e
            strehl, ee50, origin = strehl_550, ee50_550, "MAVISIM"
        else:
            core, corr, halo = build_components(lam, theta)

            strehl_target = float(
                np.exp(-(2 * np.pi * sigma_nm / (lam * 1000.0)) ** 2))

            # How much of the non-core light sits in the AO-corrected halo
            # rather than in the raw seeing halo. This has to fall towards
            # the blue, where the loop corrects a smaller fraction of the
            # turbulence, so it is scaled with the Strehl relative to the
            # 550 nm calibration point.
            split = float(np.clip(halo_split * strehl_target / strehl_550,
                                  0.0, 1.0))

            a = core_fraction(strehl_target, core, corr, halo, split)
            a = float(np.clip(a, 0.0, 1.0))
            rest = 1.0 - a
            b = rest * split
            c = rest - b

            psf = unit_energy(a * core + b * corr + c * halo)

            perfect = unit_energy(core)
            strehl = psf.max() / perfect.max()
            ee50 = ensquared(psf, PIX_SCALE, EE_BOX)
            origin = "analytic"

        # FWHM of the core, measured on the central row
        prof = psf[half, :]
        above = np.where(prof >= 0.5 * prof.max())[0]
        fwhm_mas = (above[-1] - above[0] + 1) * PIX_SCALE * 1000.0

        print(f"{lam:8.2f} {strehl:8.3f} {ee50:8.3f} {fwhm_mas:10.1f}"
              f" {origin:>10s}")

        hdu = fits.ImageHDU(psf.astype(np.float32))
        plane_header(hdu, lam, half, strehl, ee50)
        hdus.append(hdu)

    fits.HDUList(hdus).writeto(OUT_PATH, overwrite=True)
    size_mb = OUT_PATH.stat().st_size / 1024 ** 2
    print(f"wrote {OUT_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
