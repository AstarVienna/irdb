"""Choose the default wavelength and spectral bin width for each MAVIS IFU mode.

Three constraints have to be satisfied at once.

**1. Resolving power.** The delivered R must match the published value. The
``LineSpreadFunction`` effect convolves ``Box1DKernel(lsf_width)`` with a
fixed ``Gaussian1DKernel(stddev=1 bin)``, so the delivered FWHM is not
``lsf_width`` itself. ``Box1DKernel`` discretises to odd integer arrays, which
makes the delivered FWHM a step function of ``lsf_width``; ``MAVIS_IFU.yaml``
uses ``lsf_width = 2.0``, which sits in the middle of a plateau at
``FWHM_BINS`` bins. One resolution element is therefore ``FWHM_BINS`` bins and
the ideal bin width is ``wavelen / (R * FWHM_BINS)``.

Note this is tied to ``wavelen``, not to the centre of the arm: R is quoted at
the observed wavelength. Since the bin width is fixed per configuration, the
delivered R scales as ``lambda / wavelen`` if the window is retuned - about
5 % over a typical move. That is a limitation of the fixed-grid cube, and is
documented in the package README.

**2. The window must not cross a PSF plane boundary.** A PSF effect splits the
FieldOfView at the midpoints between the wavelength planes of its FITS file
(``PSF_MAVIS_mcao.fits`` has planes at 0.40, 0.55, 0.70, 0.85, 1.00 um, so
midpoints at 0.475, 0.625, 0.775, 0.925). The cube modes cannot survive such a
split: each sub-FieldOfView is checked against the single ``DetectorList3D``
NAXIS3 and the run aborts on an assertion. Centring the window on a PSF plane
maximises the room on both sides.

**3. A ScopeSim floating-point trap.** ``DetectorList3D`` rounds its wavelength
range to 7 decimals, and ``FieldOfView.make_hdu`` then computes the number of
cube planes as::

    n_wave = int((wave_max - wave_min) / spectral_bin_width)

Since the range *is* ``z_size * spectral_bin_width`` by construction, that
quotient should be exactly ``z_size``. In IEEE-754 it usually comes out as
``2047.9999999999998`` instead, the truncation drops a plane, and the same
NAXIS3 assertion fails. About half of all candidate bin widths land on the bad
side. The available margin is bounded by the rounding granularity, 5e-8 um
divided by the bin width, i.e. a few thousandths of a bin, so there is no
structurally safe choice and changing ``z_size`` does not help. The fix belongs
upstream (``round`` rather than ``int``, or taking the count from the detector
header). Until then this script picks a bin width that lands on the safe side,
and the IFU tests fail loudly if the choice ever stops working.

Run from the repository root::

    python MAVIS/background_info/tune_ifu_binning.py
"""

FWHM_BINS = 3.016      # measured FWHM of the LSF kernel at lsf_width = 2.0
Z_SIZE = 2048          # z_size in FPA_mavis_ifu_layout.dat
TOLERANCE = 0.001      # fractional deviation allowed in the bin width

# Wavelength planes of PSF_MAVIS_mcao.fits [um]
PSF_PLANES = (0.40, 0.55, 0.70, 0.85, 1.00)

# key, label, published R, default wavelen, arm wave_min, arm wave_max [um]
CONFIGS = [
    ("LR_BLUE", "LR-Blue", 5900, 0.550, 0.370, 0.720),
    ("LR_RED", "LR-Red", 5900, 0.700, 0.510, 0.935),
    ("HR_BLUE", "HR-Blue", 14700, 0.518, 0.425, 0.550),
    ("HR_RED", "HR-Red", 11500, 0.700, 0.630, 0.880),
]


def psf_split_edges(planes=PSF_PLANES):
    """Wavelengths at which a PSF effect splits the FieldOfView."""
    return [0.5 * (a + b) for a, b in zip(planes[:-1], planes[1:])]


def plane_count_quotient(z_size, dwave):
    """Reproduce the quotient ScopeSim truncates with ``int()``."""
    span = round(z_size * dwave, 7)      # DetectorList3D._get_fov_limits
    return span / dwave                  # FieldOfView.make_hdu


def is_safe(z_size, dwave):
    return int(plane_count_quotient(z_size, dwave)) == z_size


def best_bin_width(wavelen, resolving_power, z_size=Z_SIZE,
                   tolerance=TOLERANCE):
    """Bin width closest to ideal that survives the truncation."""
    ideal = wavelen / (resolving_power * FWHM_BINS)
    lo = int(ideal * (1 - tolerance) * 1e9)
    hi = int(ideal * (1 + tolerance) * 1e9)

    candidates = [k / 1e9 for k in range(lo, hi + 1)]
    safe = [d for d in candidates if is_safe(z_size, d)]
    if not safe:
        raise ValueError(
            f"no safe bin width within {tolerance:.1%} of {ideal:.6e} um")

    # They are all within tolerance of ideal, so pick the largest margin.
    return max(safe, key=lambda d: plane_count_quotient(z_size, d) - z_size)


def check_window(wavelen, dwave, arm_lo, arm_hi, z_size=Z_SIZE):
    """Return (fits_in_arm, crosses_psf_edge, wave_min, wave_max)."""
    half = 0.5 * z_size * dwave
    wmin, wmax = wavelen - half, wavelen + half
    in_arm = arm_lo <= wmin and wmax <= arm_hi
    crosses = any(wmin < edge < wmax for edge in psf_split_edges())
    return in_arm, crosses, wmin, wmax


def main():
    print(f"z_size = {Z_SIZE}, LSF FWHM = {FWHM_BINS} bins")
    print(f"PSF split edges: {psf_split_edges()}\n")

    header = (f"{'config':9s} {'wavelen':>8s} {'dwave [um]':>13s} {'margin':>8s} "
              f"{'R':>8s} {'target':>7s} {'dev':>7s} {'window [um]':>17s} "
              f"{'arm':>5s} {'psf':>5s}")
    print(header)
    print("-" * len(header))

    ok = True
    for key, label, resolving_power, wavelen, arm_lo, arm_hi in CONFIGS:
        dwave = best_bin_width(wavelen, resolving_power)
        margin = plane_count_quotient(Z_SIZE, dwave) - Z_SIZE
        delivered = wavelen / (FWHM_BINS * dwave)
        in_arm, crosses, wmin, wmax = check_window(
            wavelen, dwave, arm_lo, arm_hi)
        ok &= in_arm and not crosses
        print(f"{label:9s} {wavelen:8.3f} {dwave:13.4e} {margin:8.4f} "
              f"{delivered:8.0f} {resolving_power:7d} "
              f"{100 * (delivered / resolving_power - 1):6.2f}% "
              f"{wmin:8.4f}-{wmax:8.4f} {'ok' if in_arm else 'BAD':>5s} "
              f"{'ok' if not crosses else 'BAD':>5s}")

    print("\nPaste the bin widths into the spectral_bin_width field of the "
          "matching MAVIS_IFU_<config>.yaml,\nand the wavelengths into the "
          "matching mode in default.yaml.")
    if not ok:
        raise SystemExit("one or more windows fall outside their arm or "
                         "cross a PSF plane boundary")


if __name__ == "__main__":
    main()
