# This little script was needed to re-write the table of contents header for the MAAT IFU traces file

def update_maat_toc_hdu():
    from astropy.io import fits
    from astropy.table import Table

    toc = Table(data=[[f"Slice_{i+1}" for i in range(28)],
                      [i+2 for i in range(28)],
                      [i for i in range(28)],
                      [0 for _ in range(28)]],
                names=["description", "extension_id", "aperture_id", "image_plane_id"])
    toc_hdu = fits.table_to_hdu(toc)

    hdulist = fits.open("../MAAT_traces/R2000B_MAAT_TRACE.fits", mode="update")
    hdulist[1] = toc_hdu
    hdulist.flush()
