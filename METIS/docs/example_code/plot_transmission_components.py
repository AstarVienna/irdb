import scopesim as sim
import matplotlib.pyplot as plt

sim.rc.__config__["!SIM.file.local_packages_path"] = "../../../"
metis = sim.OpticalTrain("METIS")

metis.optics_manager.surfaces_table.plot()
metis.optics_manager.system_transmission.plot()
plt.show()