import numpy as np
import matplotlib.pyplot as plt

from scopesim.effects import SpectralTraceList, DetectorList
from scopesim import rc


def xy_from_xilam(trace_list, wavelengths, slit_coords=[0]):
    """
    Returns a grid of x,y focal plane coords for the grid of [wave, slit_coords]

    Parameters
    ----------
    trace_list : scopesim.SpectralTraceList
        Spectral trace list objects containing the description of the traces
    wavelengths : list or 1D-array
        [um]
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
                    - "waves" : list
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
                traces_dict[key] = {"waves": dic["wavelengths"][mask],
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
    guess_tbls = []
    for key, trace_dict in detector_dict[detector_id]["traces"].items():
        len_trace = len(trace_dict["waves"])
        rec_arr = np.recarray(shape=len_trace,
                               dtype=[("wlc", ">f8"),      # Wavelength (before fit)
                                      ("wll", ">f8"),      # Wavelength (after fit)
                                      ("posc", ">f8"),     # Pixel Position (before fit)
                                      ("posm", ">f8"),     # Pixel Position (after fit)
                                      ("xfirst", ">i2"),   # first pixel of the line
                                      ("xlast", ">i2"),    # last pixel of the line
                                      ("width", ">f8"),    # width of the line in pixels
                                      ("height", ">f8"),   # relative strength of the line
                                      ("order", ">i2"),    # echelle order the line is found in
                                      ("flag", "?")        # flag that tells us if we should use the line or not)
                                      ])

        rec_arr["wlc"] = trace_dict["waves"]
        rec_arr["wll"] = trace_dict["waves"]
        rec_arr["posc"] = trace_dict["y_pix"].flatten()     # !!! This is because the MICADO traces are verticle, and pyreduce likes horizontal traces. I guess we need to flip the detecotr arrays for Pyreduce?
        rec_arr["posm"] = rec_arr["posc"]                   # !!! inital guess can be the same as posm?
        rec_arr["width"] = 5
        rec_arr["height"] = 1                               # !!! This should probably be the line intensity, I think?
        rec_arr["xfirst"] = rec_arr["posc"] - rec_arr["width"]         # !!! Based on nirspec_K2.npz, this is the intial guess for +/- hwhm of the line (?)
        rec_arr["xlast"] = rec_arr["posc"] + rec_arr["width"]
        rec_arr["order"] = ["".join(key.split("_")[-2:])] * len_trace
        rec_arr["flag"] = [True] * len_trace

        guess_tbls += [rec_arr]

    comb_recarray = np.hstack(guess_tbls)

    return comb_recarray


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

################################################################################
# TESTING MAIN FUNCTION
################################################################################

if __name__ == "__main__":
    """
    Get the trace coordinates for whatever wavelengths we want
    Replace `my_wavelength` with the desired line list
    - Default here is a contant sampling of IJ filter with 1 nm bins 
    Slit edges are: 
    - IJ filter: [-1.5, 1.5] for 3" slit 
    - HK filter: [-1.5, 1.5] for 3" slit
    - HK filter: [-1.5, 13.5] for 15" slit
    By default I pass the centre of the slit (i.e. 0)
    
    """
    my_wavelengths = np.arange(0.78, 1.64, 0.001)           # equidistant samlpling for the IJ filter
    slit_coords = [0]

    # Load the Trace List and the Detector List from the MICADO package
    det_list = DetectorList(filename="../FPA_array_layout.dat")
    trace_list = SpectralTraceList(filename="../TRACE_MICADO.fits",
                                   wave_colname="wavelength",
                                   s_colname="xi",
                                   col_number_start=1,
                                   pixel_scale=0.004,
                                   plate_scale=0.2666666667)

    xy_dict = xy_from_xilam(trace_list=trace_list,
                            wavelengths=my_wavelengths,
                            slit_coords=slit_coords)
    detector_dict = pixel_from_mm(detector_list=det_list,
                                  xy_dict=xy_dict)

    comb_recarray = make_pyreduce_guess_recarray(detector_dict, detector_id=5)

    print(comb_recarray)
    print(comb_recarray.dtype)

    # comb_recarray should be saved to disk as an .npz file with the array name
    # "cs_lines" so that it is compatible with PyReduce.
    # See https://pyreduce-astro.readthedocs.io/en/latest/wavecal_linelist.html


    # plot_xy_dict(xy_dict)
    # plot_detector_xy_mm(detector_dict)
    # plot_traces_xy_pix(detector_dict)
