import os.path as pth
import scopesim as sim
from scopesim import rc
from scopesim.utils import write_report
from scopesim.reports.rst_utils import table_to_rst


rc.__config__["!SIM.reports.image_path"] = "images/"
rc.__config__["!SIM.reports.rst_path"] = "rst/"
rc.__config__["!SIM.reports.latex_path"] = "tex/"
rc.__config__["!SIM.file.local_packages_path"] = "../../"


def summary_effects(opt_mgr, filename=None, rst_title_chars="_^#*+"):
    rst_text = """Summary of Effects in Optical Elements:
{}

.. table::
    :name: tbl:effects_summary

{}
""".format(rst_title_chars[1] * 39,
           table_to_rst(opt_mgr.list_effects(), indent=4))

    fname = pth.join(rc.__config__["!SIM.reports.rst_path"], filename)
    write_report(rst_text, fname, output="rst")

    return rst_text


def summary_cmds(opt_mgr, filename=None, rst_title_chars="_^#*+"):
    rst_text = """Summary of Effects in Optical Elements:
{}

.. table::
    :name: tbl:effects_summary

{}
""".format(rst_title_chars[1] * 39,
           table_to_rst(opt_mgr.list_effects(), indent=4))

    fname = pth.join(rc.__config__["!SIM.reports.rst_path"], filename)
    write_report(rst_text, fname, output="rst")

    return rst_text


def make_micado_rst_files():

    all_modes = ["SCAO", "MCAO", "IMG_4mas", "IMG_1.5mas",   # "IMG_HCI",
                 "SPEC_3000x50"]

    cmd = sim.UserCommands(use_instrument="MICADO", set_modes=all_modes)

    opt_els = []
    for yaml in cmd.yaml_dicts:
        if yaml["alias"] != "OBS":
            opt_el = sim.optics.OpticalElement(yaml_dict=yaml)
            opt_els += [opt_el]
            fname = pth.join(rc.__config__["!SIM.reports.rst_path"],
                             "pipe_{}.rst".format(opt_el.meta["name"]))
            opt_el.report(filename=fname)

    opt_man = sim.optics.OpticsManager(None)
    opt_man.optical_elements = opt_els
    summary_effects(opt_man, filename="pipe_summary.rst")


def make_micado_sci_rst_files():
    all_modes = ["SCAO", "MCAO", "IMG_1.5mas", "IMG_4mas", "SPEC"]

    cmd = sim.UserCommands(use_instrument="MICADO_Sci", set_modes=all_modes)
    rc.__currsys__ = cmd

    opt_els = []
    for yaml in cmd.yaml_dicts:
        if yaml["alias"] in ["INST", "DET"]:
            opt_el = sim.optics.OpticalElement(yaml_dict=yaml)
            opt_els += [opt_el]
            fname = pth.join(rc.__config__["!SIM.reports.rst_path"],
                             "sci_{}.rst".format(opt_el.meta["name"]))
            opt_el.report(filename=fname)

    opt_man = sim.optics.OpticsManager(None)
    opt_man.optical_elements = opt_els
    summary_effects(opt_man, filename="sci_summary.rst")


make_micado_rst_files()
# make_micado_sci_rst_files()
