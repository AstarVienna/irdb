from astropy.io import fits
import anisocado as aniso
import argparse


def make_standard_scao_constpsf(psf_size: int = 256, offset: float = 5.0):
    waves = [1.2, 1.6, 2.15]
    psfs = []
    offset = 5

    # override header to place PSF in the centre of the WCS
    hdukeys = {
        "CRPIX1" : int(psf_size/2) + 1,
        "CRPIX2" : int(psf_size/2) + 1,
        "CRVAL1" : 0,
        "CRVAL2" : 0,
    }

    for wave in waves:
        psf = aniso.AnalyticalScaoPsf(pixelSize=0.004, N=psf_size, wavelength=wave)
        psf.shift_off_axis(0, offset)
        hdr = psf.hdu.header
        hdr.update(hdukeys)
        psfs += [fits.ImageHDU(psf.hdu.data, header=hdr)]

    keys = {"AUTHOR" : "Kieran Leschinski",
            "DATE_CRE" : "2019-07-30",
            "DATE_MOD" : "2019-07-30",
            "SOURCE" : "AnisoCADO",
            "STATUS" : "Best guess for a standard observations",
            "ETYPE" : "CONSTPSF",
            "ECAT" : (-1, "Field constant. No layer catalogue"),
            "EDATA" : (1, "PSFs begin from EXT 1"),
            "XOFFSET": (0, "[arcsec] offset from NGS"),
            "YOFFSET": (offset, "[arcsec] offset from NGS"),
            }

    pri = fits.PrimaryHDU()
    pri.header.update(keys)

    hdus = fits.HDUList([pri] + psfs)
    hdus.writeto(f"SCAO_ConstPSF_{offset}off_{psf_size}.fits", overwrite=True)
    print(hdus.info())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--psfsize', help='size of the PSF image in pixels',
                        type=int, default=256)
    parser.add_argument('--offset',
                        help='psf offset from optical axis in arcseconds',
                        type=float, default=5.0)
    parser.print_usage()
    args = parser.parse_args()

    make_standard_scao_constpsf(args.psfsize, args.offset)