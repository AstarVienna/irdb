from astropy.io import fits
import scopesim as sim


class TestHeaders:
    def test_extension_incremental_headers_count_up(self):
        sim.rc.__config__["!SIM.file.local_packages_path"] = "F:\Work\irdb"
        micado = sim.OpticalTrain("MICADO")

        hdul = fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(), fits.ImageHDU()])
        hdul = micado["extra_fits_keywords"].apply_to(hdul, optical_train=micado)
        # keys = micado["extra_fits_keywords"].dict_list[1]["keywords"]

        for i, hdu in enumerate(hdul):
            if isinstance(hdu, fits.ImageHDU):
                assert hdu.header["EXTNAME"] == f"DET{i}.DATA"
