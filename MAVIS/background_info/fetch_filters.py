"""Regenerate MAVIS/filters/TC_filter_*.dat from the SVO Filter Profile Service.

MAVIS is not built yet, so no measured MAVIS filter transmissions exist. This
script pulls the best available stand-ins and writes them in IRDB `.dat` format.

Selection rules:

* **Filter-only curves.** ScopeSim applies the detector QE separately
  (``QuantumEfficiencyCurve`` in ``MAVIS_CCD.yaml``) and the telescope
  reflectivity via the ``VLT`` package, so a profile that already folds in a
  CCD response would double-count. Every profile below has SVO
  ``components = Filter``.
* **Bessell BVRI** come from FORS2, i.e. real ESO-measured glass on a VLT
  instrument, in preference to the generic 21-point Bessell passbands.
* **SDSS u'g'r'i'z'** come from the USNO 40-inch filter-only measurements that
  define the SDSS primed system. The Paranal/OmegaCAM ugriz curves were
  rejected because SVO flags them as "filter + CCD".

Run from the repository root:

    python MAVIS/background_info/fetch_filters.py
"""

import io
import urllib.request
from datetime import date
from pathlib import Path

import numpy as np
from astropy.io.votable import parse_single_table

SVO_URL = "http://svo2.cab.inta-csic.es/theory/fps/fps.php?ID={}"
FILTER_DIR = Path(__file__).resolve().parent.parent / "filters"

# MAVIS filter name -> (SVO filter ID, human description)
FILTERS = {
    "B": ("Paranal/FORS2.ESO1074",
          "Bessell B, ESO filter #1074 as measured for VLT/FORS2"),
    "V": ("Paranal/FORS2.ESO1075",
          "Bessell V, ESO filter #1075 as measured for VLT/FORS2"),
    "R": ("Paranal/FORS2.ESO1076",
          "Bessell R, ESO filter #1076 as measured for VLT/FORS2"),
    "I": ("Paranal/FORS2.ESO1077",
          "Bessell I, ESO filter #1077 as measured for VLT/FORS2"),
    "u": ("SLOAN/SDSS.uprime_filter",
          "SDSS u' filter-only transmission (USNO 40-inch measurement)"),
    "g": ("SLOAN/SDSS.gprime_filter",
          "SDSS g' filter-only transmission (USNO 40-inch measurement)"),
    "r_SDSS": ("SLOAN/SDSS.rprime_filter",
               "SDSS r' filter-only transmission (USNO 40-inch measurement)"),
    "i_SDSS": ("SLOAN/SDSS.iprime_filter",
               "SDSS i' filter-only transmission (USNO 40-inch measurement)"),
    "z": ("SLOAN/SDSS.zprime_filter",
          "SDSS z' filter-only transmission (USNO 40-inch measurement)"),
}


def fetch(svo_id):
    """Return (wavelength_um, transmission, svo_params) for one SVO filter."""
    with urllib.request.urlopen(SVO_URL.format(svo_id), timeout=60) as resp:
        raw = resp.read()
    table = parse_single_table(io.BytesIO(raw))

    params = {}
    for param in table.params:
        params.setdefault(param.name, param.value)

    data = table.array
    wave_um = np.asarray(data["Wavelength"], dtype=float) / 1e4  # AA -> um
    trans = np.asarray(data["Transmission"], dtype=float)

    if trans.max() > 1.5:  # a few SVO profiles are in percent
        trans = trans / 100.0

    order = np.argsort(wave_um)
    return wave_um[order], trans[order], params


def write_dat(name, wave_um, trans, svo_id, description, params):
    """Write one IRDB-format filter transmission file."""
    today = date.today().isoformat()
    ref = params.get("ProfileReference") or "http://svo2.cab.inta-csic.es/theory/fps/"
    comps = params.get("components", "Filter")

    header = [
        "# author : MAVIS package",
        f"# source : SVO Filter Profile Service, filter ID {svo_id}",
        f"# source_reference : {ref}",
        f"# source_components : {comps}",
        f"# date_created  : {today}",
        f"# date_modified : {today}",
        "# type : filter:transmission",
        "# status : development",
        f"# description : {description}. Stand-in for the not-yet-measured "
        "MAVIS filter of the same name; filter glass only, detector QE and "
        "telescope reflectivity are applied separately by ScopeSim.",
        "# wavelength_unit : um",
        "# changes :",
        f"# - {today} Fetched from SVO, replacing the earlier top-hat approximation",
        "wavelength  transmission",
    ]

    lines = header + [f"{w:.6f}  {t:.6f}" for w, t in zip(wave_um, trans)]
    path = FILTER_DIR / f"TC_filter_{name}.dat"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def main():
    FILTER_DIR.mkdir(exist_ok=True)
    for name, (svo_id, description) in FILTERS.items():
        wave_um, trans, params = fetch(svo_id)
        path = write_dat(name, wave_um, trans, svo_id, description, params)
        print(f"{name:8s} {svo_id:28s} {len(wave_um):5d} pts  "
              f"{wave_um.min():.3f}-{wave_um.max():.3f} um  "
              f"peak {trans.max():.3f}  -> {path.name}")


if __name__ == "__main__":
    main()
