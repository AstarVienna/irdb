import scopesim as sim
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.table import Table, Column
import numpy as np

sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../"

def plot_throughputs_per_detector(ax, mode, wave_min, wave_max):

    cmds = sim.UserCommands(use_instrument="METIS", set_modes=[mode],
                            properties={"!OBS.filter_name": "open"})
    metis = sim.OpticalTrain(cmds)

    system_thru = metis.optics_manager.system_transmission
    surface_tbl = metis.optics_manager.surfaces_table

    waves = np.logspace(np.log10(wave_min), np.log10(wave_max), 1000) * u.um
    throughputs = {"wavelength": waves, "full_system": system_thru(waves)}
    for name, surface in surface_tbl.surfaces.items():
        throughputs[name] = surface.throughput(waves)

    for key, thru in throughputs.items():
        if not any(x in key for x in ["CFO", "IMG", "wave", "full", "ELT", "wheel", "cold"]):
            ax.plot(waves, thru, label=key, lw=1, ls="-.")

    for sub in ["CFO", "IMG", "ELT"]:
        sub_thrus = [thru for key, thru in throughputs.items() if sub in key]
        sub_thru = np.prod(sub_thrus, axis=0)
        ax.plot(waves, sub_thru, label=sub, lw=1, ls="-")

    for key, thru in throughputs.items():
        if "full" in key:
            ax.plot(waves, thru, label=key, lw=2, ls="-", c="k")

    ax.set_xlabel("Wavelength [um]")
    ax.set_ylabel("Throughput")
    ax.set_title(f"Mode: {mode}")
    ax.set_xlim(wave_min, wave_max)
    ax.set_ylim(0,1)

fig, axs = plt.subplots(1, 2, figsize=(15,6))

for ax, mode, (wave_min, wave_max) in zip(axs,
                                          ["img_lm", "img_n"],
                                          [(2.7, 5.45), (7, 14)]):
    plot_throughputs_per_detector(ax, mode, wave_min, wave_max)

axs[1].legend(loc=4)

fig.tight_layout()
fig.savefig("metis_throughput.pdf", format="pdf", overwrite=True)
plt.show()



