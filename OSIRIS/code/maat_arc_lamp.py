from synphot import SourceSpectrum
from astropy import units as u
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

import scopesim as sim
from scopesim_templates.misc import uniform_source


sim.rc.__config__["!SIM.file.local_packages_path"] = "F:/Work/irdb/"

cmds = sim.UserCommands(use_instrument="OSIRIS", set_modes=["MAAT"])
cmds.cmds["!OBS.exptime"] = 60
cmds.cmds["!OBS.dit"] = 60
cmds.cmds["!OBS.ndit"] = 1
cmds.cmds["!OBS.grating_name"]='R2000B'
osiris = sim.OpticalTrain(cmds)
osiris["lapalma_skycalc_curves"].include = False
arcspec = SourceSpectrum.from_file('OSIRIS_stitchedArc.dat')
arc = uniform_source(sed=arcspec, filter_curve='V', amplitude=16*u.ABmag, extend=520)
osiris.observe(arc)

plt.imshow(osiris.image_planes[0].data, norm=LogNorm())
plt.show()