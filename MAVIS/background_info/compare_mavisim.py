"""Compare the MAVIS ScopeSim/IRDB package against MAVISIM.

MAVISIM (Monty et al. 2021, MNRAS 507, 2192) is the MAVIS consortium's
image simulator: monochromatic V band (550 nm), end-to-end MCAO PSFs from
LQG tomography simulations, flat throughput factors. This script feeds the
same stellar field with the same photon fluxes to both simulators and
compares the results:

1. PSF metrics — ensquared energy, Strehl, FWHM — of the package PSF, the
   MAVISIM e2e reference PSF, the previous analytic package PSF (if still
   present) and a cached TipTop PSF (if present).
2. Noiseless V-band images of a 4x4 star grid (V = 16..23), compared star
   by star with aperture photometry in 50, 150 and 500 mas boxes.
3. Sky background levels under matched assumptions.

Conventions for the photometric comparison
------------------------------------------
The "input flux" handed to MAVISIM is the photon rate collected by the
VLT aperture *after* atmosphere and filter::

    flux_i = integral( spec_i(lam) T_atm(lam) T_filt(lam) dlam ) * A_tel

with the identical spectra, atmospheric curve, filter curve and telescope
area (8.2 m / 1.0 m obstruction) that ScopeSim uses. MAVISIM then applies
its own flat throughputs (VLT 0.75 x AOM 0.63 x QE 0.89), while ScopeSim
applies its wavelength-dependent curves; the comparison therefore measures
how well the two packages' *throughput chains and PSFs* agree, not how well
we can copy inputs from one to the other.

Requirements: scopesim + the MAVIS/VLT/Paranal packages, mavisim (editable
install of https://github.com/smonty93/MAVISIM), network access for skycalc.

Run from the irdb repository root::

    python MAVIS/background_info/compare_mavisim.py
"""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

from astropy import units as u
from astropy.io import ascii as ioascii
from astropy.io import fits
from astropy.table import Table

import scopesim
from scopesim import rc

PATH_HERE = Path(__file__).resolve().parent
PATH_IRDB = PATH_HERE.parent.parent
rc.__config__["!SIM.file.local_packages_path"] = str(PATH_IRDB)

MAVIS_DIR = PATH_HERE.parent
OUT_DIR = MAVIS_DIR / "docs" / "mavisim_comparison"

MAVISIM_E2E_PSF = Path("D:/Repos/MAVISIM/tests/test_psf_e2e.fits")
TIPTOP_CACHE = PATH_HERE / "tiptop_MAVIS_550nm_5b51a63de175a0f2.fits"

# --- shared physical conventions --------------------------------------------
TEL_AREA_CM2 = np.pi * ((820.0 / 2) ** 2 - (100.0 / 2) ** 2)
PIX_SCOPESIM = 0.00736      # [arcsec]
PIX_MAVISIM = 0.0075        # [arcsec] MAVISIM detector sampling
PIX_FINE = 0.00375          # [arcsec] MAVISIM internal / e2e PSF sampling

# MAVISIM's flat throughput factors (test_parameters.py)
MAVISIM_VLT = 0.75
MAVISIM_AOM = 0.63
MAVISIM_QE = 0.89

# --- the comparison field ----------------------------------------------------
GRID_XY = [-6.0, -2.0, 2.0, 6.0]              # [arcsec]
MAGS = np.arange(16.0, 24.0)                  # V = 16..23, one per star
EXP_TIME = 10.0                               # [s]
BOXES = [0.050, 0.150, 0.500]                 # [arcsec] photometry boxes
FIELD_W = 15.0                                # [arcsec] compared region


def star_field():
    """Star positions and magnitudes: 4x4 grid, V = 16..23 (twice)."""
    xs, ys, mags = [], [], []
    k = 0
    for y in GRID_XY:
        for x in GRID_XY:
            xs.append(x)
            ys.append(y)
            mags.append(MAGS[k % len(MAGS)])
            k += 1
    return np.array(xs), np.array(ys), np.array(mags)


# =============================================================================
# PSF metrics
# =============================================================================

def ensquared_curve(psf, pix, boxes):
    """Ensquared energy in centred boxes [arcsec], unit-sum normalised."""
    p = psf / psf.sum()
    c0, c1 = p.shape[0] // 2, p.shape[1] // 2
    out = []
    for box in boxes:
        half = int(round(0.5 * box / pix))
        out.append(p[c0 - half:c0 + half + 1, c1 - half:c1 + half + 1].sum())
    return np.array(out)


def measure_fwhm(psf, pix):
    prof = psf[np.unravel_index(np.argmax(psf), psf.shape)[0], :]
    above = np.where(prof >= 0.5 * prof.max())[0]
    return (above[-1] - above[0] + 1) * pix * 1000.0


def diffraction_peak(pix_scale, lam_um=0.55, d_tel=8.2, d_obs=1.0):
    """Peak of the unit-energy diffraction PSF at the given sampling."""
    n_fft = 4096
    arcsec = np.pi / (180 * 3600)
    dx = lam_um * 1e-6 / (n_fft * pix_scale * arcsec)
    axis = (np.arange(n_fft) - n_fft // 2) * dx
    xx, yy = np.meshgrid(axis, axis)
    rr = np.hypot(xx, yy)
    pupil = ((rr <= d_tel / 2) & (rr >= d_obs / 2)).astype(float)
    psf = np.abs(np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(pupil)))) ** 2
    return psf.max() / psf.sum()


def collect_psfs():
    """Return {label: (psf_2d, pixel_scale)} of all available 550 nm PSFs."""
    psfs = {}

    with fits.open(MAVISIM_E2E_PSF) as hdul:
        psfs["MAVISIM e2e (reference)"] = (
            hdul[1].data.astype(float), hdul[1].header["PIXSIZE"])

    with fits.open(MAVIS_DIR / "PSF_MAVIS_mcao.fits") as hdul:
        plane = next(h for h in hdul[1:] if h.header["WAVE0"] == 0.55)
        psfs["IRDB package (new)"] = (
            plane.data.astype(float), plane.header["CDELT1"])

    old = MAVIS_DIR / "PSF_MAVIS_analytic.fits"
    if old.exists():
        with fits.open(old) as hdul:
            plane = next(h for h in hdul[1:] if h.header["WAVE0"] == 0.55)
            psfs["IRDB package (old analytic)"] = (
                plane.data.astype(float), plane.header["CDELT1"])

    if TIPTOP_CACHE and Path(TIPTOP_CACHE).exists():
        with fits.open(TIPTOP_CACHE) as hdul:
            psfs["TipTop (default MAVIS config)"] = (
                hdul[1].data.astype(float), hdul[1].header["CDELT1"])

    return psfs


def compare_psfs():
    """PSF metrics table + EE / radial profile figure."""
    psfs = collect_psfs()
    boxes = np.array([0.0075, 0.015, 0.025, 0.05, 0.075, 0.10, 0.15,
                      0.25, 0.40, 0.60, 0.90, 1.5])

    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for label, (psf, pix) in psfs.items():
        ee = ensquared_curve(psf, pix, boxes)
        strehl = psf.max() / psf.sum() / diffraction_peak(pix)
        fwhm = measure_fwhm(psf / psf.sum(), pix)
        rows.append((label, strehl, fwhm,
                     ee[boxes == 0.05][0], ee[boxes == 0.25][0]))
        axes[0].plot(boxes * 1000, ee, "o-", ms=3, label=label)

        prof = psf / psf.sum()
        c = prof.shape[0] // 2
        r_as = np.arange(prof.shape[1] - c) * pix
        axes[1].semilogy(r_as * 1000, prof[c, c:] / pix ** 2,
                         label=label)

    axes[0].set(xscale="log", xlabel="box side [mas]",
                ylabel="ensquared energy",
                title="Ensquared energy at 550 nm")
    axes[0].axvline(50, color="0.8", zorder=0)
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.3)
    axes[1].set(xlabel="radius [mas]", ylabel="intensity [1/arcsec$^2$]",
                title="Radial profile at 550 nm", xlim=(0, 500))
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "psf_comparison.png", dpi=150)
    plt.close(fig)

    tbl = Table(rows=rows, names=("PSF", "Strehl", "FWHM [mas]",
                                  "EE(50mas)", "EE(250mas)"))
    for col in tbl.colnames[1:]:
        tbl[col].format = ".3f"
    return tbl


# =============================================================================
# MAVISIM image
# =============================================================================

def mavisim_input_fluxes(spectra_photlam, waves_um, atm_trans, filt_trans):
    """Photon rates [ph/s] collected by the VLT through atmosphere+filter."""
    waves_aa = waves_um * 1e4
    fluxes = []
    for spec in spectra_photlam:
        integrand = spec * atm_trans * filt_trans
        fluxes.append(np.trapz(integrand, waves_aa) * TEL_AREA_CM2)
    return np.array(fluxes)


def make_mavisim_image(xs, ys, fluxes):
    """Noiseless MAVISIM V-band image in electrons (7.5 mas pixels)."""
    from mavisim import ImageGenerator, Source

    ncat = len(xs)
    input_cat = Table(data={
        "Star": np.arange(ncat),
        "RA": np.zeros(ncat), "Dec": np.zeros(ncat),
        "X": np.asarray(xs, dtype=float),
        "Y": np.asarray(ys, dtype=float),
        "Flux": np.asarray(fluxes, dtype=float),
        "PM_X": np.zeros(ncat), "PM_Y": np.zeros(ncat),
    })
    input_par = SimpleNamespace(
        input_cat=input_cat,
        gauss_offset=0.0,
        ccd_sampling=PIX_MAVISIM,
    )

    source = Source(input_par=input_par, exp_time=EXP_TIME,
                    static_dist=False, use_cov=False)
    source.build_source()

    n_fine = int(round(FIELD_W / PIX_FINE))
    with fits.open(MAVISIM_E2E_PSF) as hdul:
        psf_pix = hdul[1].data.shape[0]
    imgen = ImageGenerator(array_width_pix=n_fine + psf_pix + 2,
                           source=source, psfs_file=str(MAVISIM_E2E_PSF),
                           pixsize=PIX_FINE, gauss_width_pix=34,
                           which_psf=0, norm_psf=True)
    imgen.main()
    image = imgen.get_rebinned_cropped(rebin_factor=2,
                                       cropped_width_as=FIELD_W)

    # MAVISIM's own throughput chain: photons -> electrons
    image *= MAVISIM_VLT * MAVISIM_AOM * MAVISIM_QE
    return image


# =============================================================================
# ScopeSim image
# =============================================================================

def build_scopesim_train(psf_filename=None):
    """MAVIS optical train, optionally overriding the PSF file."""
    cmd = scopesim.UserCommands(
        use_instrument="MAVIS",
        properties={"!OBS.filter_name": "V", "!OBS.dit": EXP_TIME,
                    "!OBS.ndit": 1},
    )
    if psf_filename is not None:
        for yaml_dict in cmd.yaml_dicts:
            for eff in yaml_dict.get("effects", []):
                if eff.get("name") == "mavis_ao_psf":
                    eff["kwargs"]["filename"] = psf_filename
    opt = scopesim.OpticalTrain(cmd)
    for name in ("shot_noise", "readout_noise", "dark_current"):
        opt[name].include = False
    opt.update()
    return opt


def make_scopesim_source(xs, ys, mags):
    from scopesim_templates.stellar import stars
    return stars(filter_name="V", amplitudes=list(mags) * u.mag,
                 spec_types=["A0V"] * len(mags), x=list(xs), y=list(ys))


def scopesim_star_spectra(src, waves_um):
    """Per-star photon spectra [PHOTLAM] on the given wavelength grid."""
    field = src.fields[0]
    if hasattr(field, "field"):    # newer scopesim: field object wrapper
        tbl = field.field
    else:
        tbl = field
    spectra = []
    for row in tbl:
        spec = src.spectra[int(row["ref"])]
        weight = float(row["weight"]) if "weight" in tbl.colnames else 1.0
        spectra.append(spec(waves_um * u.um).to_value("ph s-1 cm-2 AA-1")
                       * weight)
    return spectra


def make_scopesim_image(opt, src):
    """Noiseless ScopeSim V-band readout in electrons (gain = 1)."""
    opt.observe(src, update=True)
    hdus = opt.readout()
    return hdus[0][1].data.astype(float)


# =============================================================================
# photometry
# =============================================================================

def box_photometry(image, pix, x_as, y_as, box_as, bkg_level=None):
    """Sky-subtracted flux in a box centred on (x_as, y_as) from centre."""
    if bkg_level is None:
        bkg_level = np.median(image)
    cy, cx = image.shape[0] / 2, image.shape[1] / 2
    ix = int(round(cx + x_as / pix - 0.5))
    iy = int(round(cy + y_as / pix - 0.5))
    half = int(round(0.5 * box_as / pix))
    cut = image[iy - half:iy + half + 1, ix - half:ix + half + 1]
    return float(cut.sum() - bkg_level * cut.size)


def compare_photometry(im_mavisim, im_scopesim, xs, ys, mags,
                       fluxes_ph, tag):
    """Aperture photometry ratio table + figure. Returns the table."""
    rows = []
    for x, y, mag, flux in zip(xs, ys, mags, fluxes_ph):
        for box in BOXES:
            f_mav = box_photometry(im_mavisim, PIX_MAVISIM, x, y, box)
            f_sco = box_photometry(im_scopesim, PIX_SCOPESIM, x, y, box)
            rows.append((x, y, mag, box * 1000, flux * EXP_TIME,
                         f_mav, f_sco, f_sco / f_mav))
    tbl = Table(rows=rows, names=("x", "y", "V", "box [mas]", "ph in",
                                  "e- MAVISIM", "e- ScopeSim", "ratio"))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for box in BOXES:
        sel = tbl["box [mas]"] == box * 1000
        ax.plot(tbl["V"][sel], tbl["ratio"][sel], "o",
                label=f"{box*1000:.0f} mas box", alpha=0.8)
    ax.axhline(1.0, color="k", lw=0.8)
    ax.axhspan(0.9, 1.1, color="tab:green", alpha=0.12,
               label=r"$\pm$10 %")
    ax.set(xlabel="V [mag]", ylabel="ScopeSim / MAVISIM flux ratio",
           title=f"Star-by-star aperture photometry ({tag})")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"photometry_{tag}.png", dpi=150)
    plt.close(fig)
    return tbl


def image_figure(im_mavisim, im_scopesim, tag):
    """Side-by-side log-stretch images + a zoom on one star."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.4))
    vmax = max(im_mavisim.max(), im_scopesim.max())
    vmin = vmax * 1e-6
    half_w = FIELD_W / 2
    for ax, im, pix, label in [
            (axes[0], im_mavisim, PIX_MAVISIM, "MAVISIM"),
            (axes[1], im_scopesim, PIX_SCOPESIM, f"ScopeSim ({tag})")]:
        n = im.shape[0]
        w_as = n * pix / 2
        ax.imshow(np.clip(im, vmin, None), norm=LogNorm(vmin, vmax),
                  origin="lower", extent=[-w_as, w_as, -w_as, w_as],
                  cmap="afmhot")
        ax.set(title=label, xlabel="[arcsec]", ylabel="[arcsec]",
               xlim=(-half_w, half_w), ylim=(-half_w, half_w))

    # zoomed cutout on the brightest star (V=16 at -6,-6)
    for im, pix, style in [(im_mavisim, PIX_MAVISIM, "-"),
                           (im_scopesim, PIX_SCOPESIM, "--")]:
        iy = int(round(im.shape[0] / 2 - 6.0 / pix - 0.5))
        ix = int(round(im.shape[1] / 2 - 6.0 / pix - 0.5))
        prof = im[iy, :]
        r_as = (np.arange(im.shape[1]) - ix) * pix
        axes[2].semilogy(r_as * 1000, np.clip(prof / pix**2, 1, None), style)
    axes[2].set(xlim=(-300, 300), xlabel="offset [mas]",
                ylabel="e$^-$ / arcsec$^2$",
                title="Cut through V=16 star")
    axes[2].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"images_{tag}.png", dpi=150)
    plt.close(fig)


# =============================================================================
# sky background
# =============================================================================

def compare_sky(opt):
    """Sky background levels, ScopeSim vs MAVISIM's constant-sky model."""
    from scopesim.source import source_templates as st
    from mavisim.util import add_constant_sky_pixel

    opt.observe(st.empty_sky(), update=True)
    img = opt.readout()[0][1].data.astype(float)
    sky_scopesim = float(np.median(img)) / EXP_TIME / PIX_SCOPESIM ** 2

    def mavisim_sky(surf_bright):
        input_par = SimpleNamespace(
            ccd_sampling=PIX_MAVISIM, surf_bright=surf_bright,
            psf_wavelength=550.0, filt_width=88.0,
            collecting_area=TEL_AREA_CM2 / 1e4,
        )
        per_pix = add_constant_sky_pixel(input_par, 1.0)
        per_pix *= MAVISIM_VLT * MAVISIM_AOM * MAVISIM_QE
        return per_pix / PIX_MAVISIM ** 2      # e-/s/arcsec2

    # the V-mag/arcsec2 the ScopeSim (skycalc) sky corresponds to, using the
    # same crude monochromatic zero point MAVISIM uses
    zp = mavisim_sky(0.0)
    sky_mag = -2.5 * np.log10(sky_scopesim / zp)

    rows = [
        ("ScopeSim, skycalc default (V equiv.)", sky_scopesim, sky_mag),
        ("MAVISIM, dark sky 21.61 mag/arcsec2", mavisim_sky(21.61), 21.61),
        ("MAVISIM, matched to skycalc", mavisim_sky(sky_mag), sky_mag),
    ]
    tbl = Table(rows=rows, names=("sky model", "e-/s/arcsec2", "V mag/as2"))
    tbl["e-/s/arcsec2"].format = ".2f"
    tbl["V mag/as2"].format = ".2f"
    return tbl


# =============================================================================
# main
# =============================================================================

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    xs, ys, mags = star_field()

    print("=" * 70)
    print("1. PSF metrics at 550 nm")
    print("=" * 70)
    psf_tbl = compare_psfs()
    psf_tbl.pprint_all()

    print("\n" + "=" * 70)
    print("2. V-band image comparison (noiseless)")
    print("=" * 70)
    src = make_scopesim_source(xs, ys, mags)
    opt = build_scopesim_train()

    # common ingredients for the MAVISIM input fluxes
    waves_um = np.linspace(0.42, 0.75, 2000)
    atmo = opt["skycalc_atmosphere"]
    atmo = atmo[0] if isinstance(atmo, list) else atmo
    atm_trans = np.array([float(atmo.throughput(w * u.um))
                          for w in waves_um])
    filt = ioascii.read(MAVIS_DIR / "filters" / "TC_filter_V.dat")
    filt_trans = np.interp(waves_um, filt["wavelength"],
                           filt["transmission"], left=0, right=0)

    spectra = scopesim_star_spectra(src, waves_um)
    fluxes = mavisim_input_fluxes(spectra, waves_um, atm_trans, filt_trans)
    for mag, flux in zip(mags, fluxes):
        print(f"  V={mag:.0f}: {flux:10.1f} ph/s through atm+filter")

    print("\n-- MAVISIM image ...")
    im_mavisim = make_mavisim_image(xs, ys, fluxes)
    print("-- ScopeSim image (new PSF) ...")
    im_scopesim = make_scopesim_image(opt, src)

    image_figure(im_mavisim, im_scopesim, "new_psf")
    phot_tbl = compare_photometry(im_mavisim, im_scopesim, xs, ys, mags,
                                  fluxes, "new_psf")
    phot_tbl.pprint_all()
    for box in BOXES:
        sel = phot_tbl["box [mas]"] == box * 1000
        ratios = np.array(phot_tbl["ratio"][sel])
        print(f"  {box*1000:5.0f} mas box: ScopeSim/MAVISIM = "
              f"{ratios.mean():.3f} +/- {ratios.std():.3f}")

    old_psf = MAVIS_DIR / "PSF_MAVIS_analytic.fits"
    if old_psf.exists():
        print("\n-- ScopeSim image (old analytic PSF) ...")
        opt_old = build_scopesim_train(psf_filename=str(old_psf))
        im_old = make_scopesim_image(opt_old, src)
        image_figure(im_mavisim, im_old, "old_psf")
        phot_old = compare_photometry(im_mavisim, im_old, xs, ys, mags,
                                      fluxes, "old_psf")
        for box in BOXES:
            sel = phot_old["box [mas]"] == box * 1000
            ratios = np.array(phot_old["ratio"][sel])
            print(f"  {box*1000:5.0f} mas box: ScopeSim(old)/MAVISIM = "
                  f"{ratios.mean():.3f} +/- {ratios.std():.3f}")

    print("\n" + "=" * 70)
    print("3. Sky background")
    print("=" * 70)
    sky_tbl = compare_sky(opt)
    sky_tbl.pprint_all()

    print(f"\nFigures written to {OUT_DIR}")


if __name__ == "__main__":
    main()
