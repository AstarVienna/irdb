import os
import os.path as pth
import yaml

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
    rc.__currsys__ = cmd

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


def make_package_report_files():
    # make "packages" folder in docs/source
    # make <package name> folder in docs/source/packages
    # make <package name> folder in docs/source/_static
    # open irdb/package.yaml
    # loop though the packages
    # set the !SIM.reports.rst_path and images_path
    # if package has a no default.yaml,
    # - create a single OpticalElement and generate report
    # else
    # - loop through the yamls, and exclude names that appear in packages.yaml
    # - loop through the mode_yamls, include any extra properties

    top_dir = "../../"
    source_packages = "../source/packages"
    source_static = "../source/_static"

    with open(pth.join(top_dir, "irdb/packages.yaml")) as f:
        import yaml
        pkg_names = list(yaml.full_load(f).keys())

    for pkg_name in pkg_names[:1]:
        orig_pkg_path = pth.join(top_dir, pkg_name)
        rst_save_path = pth.join(source_packages, pkg_name)
        image_save_path = pth.join(source_static, pkg_name)

        if not pth.exists(rst_save_path):
            os.mkdir(rst_save_path)
        if not pth.exists(image_save_path):
            os.mkdir(image_save_path)

        rc.__currsys__["!SIM.reports.rst_path"] = rst_save_path
        rc.__currsys__["!SIM.reports.image_path"] = image_save_path

        if "../" not in rc.__search_path__:
            rc.__search_path__.insert(0, "../")

        default_yaml = pth.join(orig_pkg_path, "default.yaml")
        if not pth.exists(default_yaml):
            default_yaml = pth.join(orig_pkg_path, "_default_standalone.yaml")

        cmd = sim.UserCommands(yamls=[default_yaml])
        rc.__currsys__ = cmd

        opt_els = []
        for yaml in cmd.yaml_dicts:
            opt_el = sim.optics.OpticalElement(yaml_dict=yaml)
            opt_els += [opt_el]
            fname = pth.join(rc.__config__["!SIM.reports.rst_path"],
                             "sci_{}.rst".format(opt_el.meta["name"]))
            opt_el.report(filename=fname)






# make_micado_rst_files()
# make_micado_sci_rst_files()
make_package_report_files()