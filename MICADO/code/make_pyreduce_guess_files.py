import os
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import ascii

from scopesim.effects import SpectralTraceList, DetectorList


def xy_from_xilam(trace_list, wavelengths, fluxes, slit_coords):
    """
    Returns a grid of x,y focal plane coords for the grid of [wave, slit_coords]

    Parameters
    ----------
    trace_list : scopesim.SpectralTraceList
        Spectral trace list objects containing the description of the traces
    wavelengths : list or 1D-array
        [um]
    fluxes : list or 1D-array
        [any units]
    slit_coords : list or 1D-array
        [arcsec] Positions along th

    Returns
    -------
    xy_dict : dict
        Contains 2D arrays for each of the x,y coords for the given wavelengths
        and slit coords (xi).
        The keys are the names of the order trace tables from the FITS file.
        The values are each a dictionary containing the following:
        - "wavelengths" : 1D array
            [um] The wavelengths that are actually covered by each trace
        - "slit_coords": 1D array
            [arcsec] The positions along the slit to be evaluated
        - "x" : 2D array
            [mm] A grid of x coords for the product of wavelength and siit_coords
        - "y" : 2D array
            [mm] Same as "x"

    Examples
    --------
    The 2D array for x has the x positions [mm] relative to the centre of the
    focal plane for each wavelength (vertical) and slit position [horizontal]
    ::

        trace_list = SpectralTraceList(filename="../TRACE_MICADO.fits",
                                       wave_colname="wavelength",
                                       s_colname="xi",
                                       col_number_start=1,
                                       pixel_scale=0.004,
                                       plate_scale=0.2666666667)
        xy_dict = xy_from_xilam(trace_list=trace_list
                                wavelengths=np.arange(0.8, 2.4, 0.1),
                                slit_coords=[0., 1.])
        print(xy_dict["ORDER_3_1"]["x"])
        [[-45.87368324 -49.77937256]
        [-49.11376953 -52.77437053]
        [-51.10904212 -54.70640935]
        [-53.09295522 -56.74625748]
        [-55.60176502 -59.36748534]]


    """
    xy_dict = {}
    for key, spt in trace_list.spectral_traces.items():
        mask = (wavelengths >= spt.wave_min) * (wavelengths <= spt.wave_max)
        waves = wavelengths[mask]
        xy_dict[key] = {"wavelengths": waves,
                        "fluxes": fluxes[mask],
                        "slit_coords": slit_coords,
                        "x": spt.xilam2x(slit_coords, waves, grid=True),
                        "y": spt.xilam2y(slit_coords, waves, grid=True)}

    return xy_dict


def pixel_from_mm(detector_list, xy_dict):
    """
    Parameters
    ----------
    detector_list: scopesim.DetectorList
        ScopeSim description of the geometry of the detectors
    xy_dict : dict of dicts
        Contains xy coords of each trace for the given wavelength list

    Returns
    -------
    detector_dict : nested dicts
        Contains the xy coords of the (centre of?) each line from the wavelength
        list for each trace on each detector.
        The dictionary has the following structure:

        - detector_dict
            - detector_id (e.g. 1)
                - "edges"
                    - "x" : list
                    - "y" : list
                - "traces"
                    - "wavelengths" : list
                    - "fluxes": list
                    - "slit_coords" : list
                    - "x_mm" : list     # relative to centre of focal plane
                    - "y_mm" : list
                    - "x_pix" : list    # relative to (0,0) pixel of each detector
                    - "y_pix" : list

    """
    detector_dict = {}
    for det in detector_list.table:
        pixel_size = det["pixel_size"]
        x0 = det["x_cen"] - (0.5 * det["x_size"] * pixel_size)
        x1 = det["x_cen"] + (0.5 * det["x_size"] * pixel_size)
        y0 = det["y_cen"] - (0.5 * det["y_size"] * pixel_size)
        y1 = det["y_cen"] + (0.5 * det["y_size"] * pixel_size)

        edges_dict = {"x": [x0, x1, x1, x0, x0],
                      "y": [y0, y0, y1, y1, y0]}
        detector_dict[det["id"]] = {"edges": edges_dict}

        traces_dict = {}
        for key, dic in xy_dict.items():
            mask = (dic["x"] >= x0) * (dic["x"] <= x1) * \
                   (dic["y"] >= y0) * (dic["y"] <= y1)
            mask = mask.prod(axis=1).astype(bool)

            if mask.sum() > 0:
                x_mm = dic["x"][mask]
                y_mm = dic["y"][mask]
                x_pix = (x_mm - x0) / pixel_size
                y_pix = (y_mm - y0) / pixel_size
                traces_dict[key] = {"wavelengths": dic["wavelengths"][mask],
                                    "fluxes": dic["fluxes"][mask],
                                    "slit_coords": dic["slit_coords"],
                                    "x_mm": x_mm,
                                    "y_mm": y_mm,
                                    "x_pix": x_pix,
                                    "y_pix": y_pix}
        detector_dict[det["id"]]["traces"] = traces_dict

    return detector_dict


def make_pyreduce_guess_recarray(detector_dict, detector_id=5):
    """
    Creates an array with the dtypes and names for a PyReduce initial guess file

    .. note:: This function DOES NOT save the recarray to disk.

    This array can be saved to disk using numpy.savez()
    See https://numpy.org/doc/stable/reference/generated/numpy.savez.html

    The array should be saved unter the variable name cs_lines
    See https://pyreduce-astro.readthedocs.io/en/latest/wavecal_linelist.html

    Parameters
    ----------
    detector_dict : dict of dicts
        Output of pixel_from_mm
    detector_id : int
        Which detector to use. Default is 5 (central detector)

    Returns
    -------
    comb_recarray : np.recarray
        A recarray in the format needed by PyReduce

    Note
    ----
    To use the output here for PyReduce, the recarray should be saved to a .npz
    file using the "cs_lines" name for the array.

    """

    x_mins = {key: trace["x_pix"][0].min()
              for key, trace in detector_dict[detector_id]["traces"].items()}
    sorted_x_mins = sorted(x_mins, key=x_mins.get)

    guess_tbls = []
    for i, order_name in enumerate(sorted_x_mins):
        trace_dict = detector_dict[detector_id]["traces"][order_name]
        len_trace = len(trace_dict["wavelengths"])
        rec_arr = np.recarray(shape=len_trace,
                               dtype=[("wlc", ">f8"),      # Wavelength (before fit)
                                      ("wll", ">f8"),      # Wavelength (after fit)
                                      ("posc", ">f8"),     # Pixel Position (before fit)
                                      ("posm", ">f8"),     # Pixel Position (after fit)
                                      ("xfirst", ">f8"),   # first pixel of the line
                                      ("xlast", ">f8"),    # last pixel of the line
                                      ("width", ">f8"),    # width of the line in pixels
                                      ("height", ">f8"),   # relative strength of the line
                                      ("order", ">i2"),    # echelle order the line is found in
                                      ("flag", "?")        # flag that tells us if we should use the line or not)
                                      ])

        rec_arr["wlc"] = trace_dict["wavelengths"] * 1e4        # [Angstrom]
        rec_arr["wll"] = trace_dict["wavelengths"] * 1e4
        rec_arr["posc"] = trace_dict["y_pix"][:, 1]             # Centre of the line. Also, Pyreduce likes horizontal traces. Please Transpose the detector frame for PyReduce.
        rec_arr["posm"] = rec_arr["posc"]
        rec_arr["width"] = 5
        rec_arr["height"] = trace_dict["fluxes"]                # Arbitrary line intensity
        rec_arr["xfirst"] = trace_dict["y_pix"].min(axis=1)     # This accounts for the shear in the lines, and that the bottom and top of the lines will be offset wrt the central pixel
        rec_arr["xlast"] = trace_dict["y_pix"].max(axis=1)
        rec_arr["order"] = [i] * len_trace
        rec_arr["flag"] = [True] * len_trace

        guess_tbls += [rec_arr]

    comb_recarray = np.hstack(guess_tbls)

    return comb_recarray


def make_npz_file(line_list_path, irdb_micado_path, npz_output_path,
                  detector_id, wave_min=0.78, wave_max=1.5,
                  slit_coords=(-1.5, 0., 1.5)):
    """
    Make the .npz file required by PyReduce based on ScopeSim files

    This is the function that drives the creation of the NPZ file.
    It can be seen as a wrapper for the old __main__ testing script.

    Parameters
    ----------
    line_list_path : str
        [nm] Path to file with wavelengths and intensities of lines.
        Note: to fit with MICADO line list, use [nm]
    irdb_micado_path : str
        Path inside the MICADO IRDB package
    npz_output_path : str
        Where to save the .npz file
    detector_id : int
        Which MICADO detector to use
    wave_min, wave_max : float, optional
        [nm] Consistency with input line list
    slit_coords : list of floats, optional
        [arcsec] The ends and middle of the slit

    Returns
    -------
    rec_array : np.recarray
        The numpy record-array needed by PyReduce

    Examples
    --------
    ::

        line_list_path = "<path/to>/masterlinelist_2.1.txt"
        irdb_micado_path = "<path/to>/irdb/MICADO"
        npz_output_path = "./HK_3arcsec_chip5.npz"

        make_npz_file(line_list_path=line_list_path,
                      irdb_micado_path=irdb_micado_path,
                      npz_output_path=npz_output_path,
                      detector_id=5,
                      wave_min=780.,
                      wave_max=1500.)

    """
    # --------------------------------------------------------------------------
    # Quickly swap directories to get the MICADO trace info

    old_working_dir = os.getcwd()
    os.chdir(irdb_micado_path)
    # Load the Trace List and the Detector List from the MICADO package
    det_list = DetectorList(filename="FPA_array_layout.dat")
    trace_list = SpectralTraceList(filename="TRACE_MICADO.fits",
                                   wave_colname="wavelength",
                                   s_colname="xi",
                                   col_number_start=1,
                                   pixel_scale=0.004,
                                   plate_scale=0.2666666667)
    os.chdir(old_working_dir)

    # --------------------------------------------------------------------------
    # Load the desired line list

    line_list = ascii.read(line_list_path)
    fluxes = np.array(line_list["Relative_Intensity"])
    waves = np.array(line_list["Wavelength"])               # input in [nm]
    mask = (waves >= wave_min) * (waves <= wave_max)
    my_wavelengths = waves[mask] * 1e-3                     # convert to [um]
    relative_flux = fluxes[mask]

    # --------------------------------------------------------------------------
    # Convert wavelengths to xy pixel positions

    xy_dict = xy_from_xilam(trace_list=trace_list,
                            wavelengths=my_wavelengths,
                            fluxes=relative_flux,
                            slit_coords=slit_coords)
    detector_dict = pixel_from_mm(detector_list=det_list,
                                  xy_dict=xy_dict)

    # --------------------------------------------------------------------------
    # Make the rec_array and write to disk

    rec_array = make_pyreduce_guess_recarray(detector_dict, detector_id)
    if npz_output_path is not None:
        np.savez(npz_output_path, cs_lines=rec_array)

    return rec_array


################################################################################
# PLOTTING FUNCTIONS
################################################################################

def plot_xy_dict(xy_dict):
    for order in xy_dict.values():
        plt.plot(order["x"].flatten(), order["y"].flatten())
    plt.xlim(-100, 100)
    plt.ylim(-100, 100)
    plt.gca().set_aspect("equal")
    plt.show()


def plot_detector_xy_mm(detector_dict):
    for i, det in enumerate(detector_dict.values()):
        for trace in det["traces"].values():
            plt.plot(trace["x_mm"].flatten(), trace["y_mm"].flatten())
        plt.plot(det["edges"]["x"], det["edges"]["y"])

    plt.xlim(-100, 100)
    plt.ylim(-100, 100)
    plt.gca().set_aspect("equal")
    plt.show()


def plot_traces_xy_pix(detector_dict):
    for i, det in enumerate(detector_dict.values()):
        plt.subplot(3, 3, i+1)
        for trace in det["traces"].values():
            plt.plot(trace["x_pix"].flatten(), trace["y_pix"].flatten())

        plt.xlim(0, 4096)
        plt.ylim(0, 4096)
        plt.gca().set_aspect("equal")
    plt.show()


def plot_rec_arrays(rec_arrays, detector_dict=None):
    for i, ra in enumerate(rec_arrays):
        plt.subplot(3, 3, i + 1)
        plt.plot(ra["posc"])

        plt.gca().set_aspect("equal")
    plt.show()


if __name__ == "__main__":
    line_list_path = "F:/Work/ScopeSim_Templates/scopesim_templates/micado/data/masterlinelist_2.1.txt"
    irdb_micado_path = "F:/Work/irdb/MICADO"
    npz_output_path = "./HK_3arcsec_chip5.npz"

    rec_array = make_npz_file(line_list_path=line_list_path,
                              irdb_micado_path=irdb_micado_path,
                              npz_output_path=None,
                              detector_id=5,
                              wave_min=780.,
                              wave_max=1500.)

    print(rec_array)
    print(rec_array.dtype)
 