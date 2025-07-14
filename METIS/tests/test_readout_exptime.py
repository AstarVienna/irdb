"""Test whether giving exptime in readout() is respected."""
import copy
import os
from matplotlib import pyplot as plt
import scopesim as sim
import numpy
import scipy

PKGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sim.rc.__config__["!SIM.file.local_packages_path"] = PKGS_DIR

PLOTS = False


def test_readout_exptime():
    """Test whether giving exptime in readout() is respected.

    The implementation of Quantization and Autoexposure has lead
    to some problems in the past:
    - The Quantization was not undone when the detector was reset
      when doing a second readout.
    - The exptime specified in readout is ignored in favor of the
      default DIT/NDIT.

    This end-to-end regression test should prevent such problems
    from reoccurring in the future.

    See also https://github.com/AstarVienna/ScopeSim/issues/438
    """

    star = sim.source.source_templates.star()
    # Shift the source, so it can be detected through center_of_mass.
    star.shift(0.5, 1.0)
    cmd_l = sim.UserCommands(use_instrument="METIS", set_modes=["img_lm"])

    # The first readout might ignore the exptime.
    metis_l = sim.OpticalTrain(cmd_l)
    metis_l["exposure_output"].set_mode("sum")
    metis_l.observe(star, update=True)
    result_first = metis_l.readout(exptime=0.1)[0]
    # We need to copy the first readeout, because
    # the second readout might overwrite the first...
    result_first_copy = copy.deepcopy(result_first)

    # The second readout might not properly have the detector reset.
    metis_l = sim.OpticalTrain(cmd_l)
    metis_l["exposure_output"].set_mode("sum")
    metis_l.observe(star, update=True)
    result_temp = metis_l.readout(exptime=.1)[0]
    result_temp_copy = copy.deepcopy(result_temp)
    assert (result_temp[1].data == result_temp_copy[1].data).all()
    result_second = metis_l.readout(exptime=.1)[0]

    if PLOTS:
        plt.figure(figsize=(10, 5))
        plt.subplot(121)
        # Plot the copy, because the original might be altered.
        plt.imshow(result_first_copy[1].data, origin='lower')
        plt.title(r"First readout")
        plt.subplot(122)
        plt.imshow(result_second[1].data, origin='lower')
        plt.title(r"Second readout")
        plt.savefig("extrareadoutornot.png")
        plt.show()

    mean_first = result_first[1].data.mean()
    data1 = numpy.abs(result_first[1].data - mean_first)
    x1, y1 = scipy.ndimage.center_of_mass(data1)
    flux1 = data1.sum()

    mean_second = result_second[1].data.mean()
    data2 = numpy.abs(result_second[1].data - mean_second)
    x2, y2 = scipy.ndimage.center_of_mass(data2)
    flux2 = data2.sum()

    print(flux1, flux2)


    assert 1090 < x2 < 1110
    assert 1050 < y2 < 1070
    assert 10**8 < flux2
    assert 1090 < x1 < 1110
    assert 1050 < y1 < 1070
    assert 10**8 < flux1

    # TOOD: fix this bug, https://github.com/AstarVienna/ScopeSim/issues/439
    # assert (result_temp[1].data == result_temp_copy[1].data).all()
