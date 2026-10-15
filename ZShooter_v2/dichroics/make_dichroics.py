import numpy as np
import astropy.units as u
from astropy.time import Time
from pathlib import Path
from scipy.stats import norm
from scipy.signal import convolve
from synphot import (ThermalSpectralElement, Empirical1D)

def make_dichroic(
        domain: tuple[float | u.Quantity, float | u.Quantity],
        transmission: float,
        reflection: float,
        min: float | u.Quantity,
        max: float | u.Quantity,
        fold: float | u.Quantity,
        transition_width: float | u.Quantity = 30,
        temperature: float | u.Quantity = 0) -> tuple[ThermalSpectralElement, ThermalSpectralElement]:
    """
    Return a matched pait of dichroic efficiency curves.
    Args:
        domain:
        min:
        max:
        fold:
        transmission:
        reflection:
        transition_width:

    Returns: (ThermalSpectralElement, ThermalSpectralElement)

    """

    domain = u.Quantity(domain)
    full_x = np.linspace(np.floor(domain.min()), np.ceil(domain.max()), num=int(np.ceil(np.ptp(domain)).value))
    full_yt = np.zeros(full_x.size)
    full_yr = np.zeros_like(full_yt)
    in_trans = (full_x >= fold)
    in_refl = (~in_trans)
    full_yt[in_trans & (full_x <= max)] = transmission
    full_yr[in_refl & (full_x >= min)] = reflection

    if not isinstance(transition_width, u.Quantity):
        transition_width = transition_width * domain.unit

    transition_sigma = transition_width / (2 * norm.ppf(0.98))

    dx = full_x[1] - full_x[0]
    kx = np.arange(-10 * transition_sigma.value, 10 * transition_sigma.value + dx.value, dx.value)
    ker = norm.pdf(kx, loc=0, scale=transition_sigma.value)
    ker /= ker.sum()

    smoothedt = convolve(full_yt, ker, mode="same")
    smoothedr = convolve(full_yr, ker, mode="same")

    return (ThermalSpectralElement(Empirical1D, points=full_x, lookup_table=smoothedr, fill_value=0, method='linear',
                                   bounds_error=False, temperature=temperature),
            ThermalSpectralElement(Empirical1D, points=full_x, lookup_table=smoothedt, fill_value=0, method='linear',
                                   bounds_error=False, temperature=temperature))


def make_zshooter_dichroics(
        channel_ranges: dict[str, u.Quantity],
        valid_domain: tuple[float, float],
        transmission: float,
        reflection: float,
        range_pad: float,
        transition_widths: dict[str, u.Quantity]):

    def fold_wavelength(reflection_channels: tuple[str, ...],
                        transmission_channels: tuple[str, ...]):
        reflection_edge = max(channel_ranges[channel].max() for channel in reflection_channels)
        transmission_edge = min(channel_ranges[channel].min() for channel in transmission_channels)
        return 0.5 * (reflection_edge + transmission_edge)

    def channel_bound(channels: tuple[str, ...], bound: str):
        values = (getattr(channel_ranges[channel], bound)() for channel in channels)
        return min(values) if bound == "min" else max(values)

    def split(name: str,
              reflection_channels: tuple[str, ...],
              transmission_channels: tuple[str, ...]):
        channels = reflection_channels + transmission_channels
        return make_dichroic(
            valid_domain,
            transmission,
            reflection,
            channel_bound(channels, "min") - range_pad,
            channel_bound(channels, "max") + range_pad,
            fold_wavelength(reflection_channels, transmission_channels),
            transition_width=transition_widths[name],
        )

    return {
        "bgr-yjhk": split("bgr-yjhk", ("b", "g", "r"), ("yj", "h", "k")),
        "b-gr": split("b-gr", ("b",), ("g", "r")),
        "yj-hk": split("yj-hk", ("yj",), ("h", "k")),
        "g-r": split("g-r", ("g",), ("r",)),
        "h-k": split("h-k", ("h",), ("k",)),
        "u-vz": split("b-gr", ("u",), ("v", "z")),
        "v-z": split("v-z", ("v",), ("z",)),
    }


def write_dichroic_curves(filename, tx_model, rx_model, header=None):
    wave = np.arange(3000, 25000, 10)
    with open(filename, 'w') as f:
        if header is not None:
            f.write(header + '\n')
        f.write('wavelength transmission reflection\n')
        for x in wave:
            f.write(f'{(x*u.AA).to(u.um).value:.3f} {tx_model(x):.6f} {rx_model(x):.6f}\n')



def read_channel_ranges(trace_parameters_path: Path) -> dict[str, u.Quantity]:
    header = None
    traces = []
    for line in trace_parameters_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if header is None:
            header = fields
            continue
        traces.append(dict(zip(header, fields)))

    return {trace["prefix"]: np.array([trace["min_wave"], trace["max_wave"]],dtype=float, ) * u.nm
            for trace in traces}


DICHROIC_PAD = 30 * u.nm
DICHROIC_TRANS = 0.985
DICHROIC_REFL = 0.985
DICHROIC_DOMAIN = (250, 2550) * u.nm
DICHROIC_DIR = Path(__file__).resolve().parent
DICHROIC_TRANS_WID = {'bgr-yjhk': 20 *u.nm,
             'b-gr': 10*u.nm,
             'g-r': 12 * u.nm,
             'yj-hk': 30 * u.nm,
             'h-k': 40 * u.nm,
             'u-vz': 10 * u.nm,
             'v-z': 12 * u.nm}

TRACE_PARAMETERS_PATH = DICHROIC_DIR.parent / "traces" / "echelle_trace_parameters.dat"



channel_range = read_channel_ranges(TRACE_PARAMETERS_PATH)
channel_range['u']=u.Quantity([300, 400])*u.nm
channel_range['v']=u.Quantity([400, 850])*u.nm
channel_range['z']=u.Quantity([850, 1100])*u.nm
dichroics = make_zshooter_dichroics(channel_range, DICHROIC_DOMAIN, DICHROIC_TRANS, DICHROIC_REFL, DICHROIC_PAD,
                                    transition_widths=DICHROIC_TRANS_WID)



##  ZImager dichroics:
hdr_zi_u = f"""# name : zimager_u_dichroic
# author : unknown
# date_created : 2026-10-15T12:00:00
# date_modified : {Time.now().isot}
# description : Transmits red, reflects u
# wavelength_unit : um
# changes :
#"""
hdr_zi_z = f"""# name : zimager_z_dichroic
# author : unknown
# date_created : 2026-10-15T12:00:00
# date_modified : {Time.now().isot}
# description : Logpass at z, reflects shorter wavelengths 
# wavelength_unit : um
# changes :
#"""
write_dichroic_curves(DICHROIC_DIR / 'TER_dichroic_u-v.dat', dichroics['u-vz'][1]._model, dichroics['u-vz'][0]._model, header=hdr_zi_u)
write_dichroic_curves(DICHROIC_DIR / 'TER_dichroic_v-z.dat', dichroics['v-z'][1]._model, dichroics['v-z'][0]._model, header=hdr_zi_z)

## First dichroic: I, splits BGR from YJHK
hdr_i = f"""# name : first_dichroic
# author : unknown
# date_created : 2026-03-16T12:00:00
# date_modified : {Time.now().isot}
# description : Transmits NIR, reflects UBVIS
# wavelength_unit : um
# changes :
#"""
write_dichroic_curves(DICHROIC_DIR / 'TER_dichroic_bgr-yjhk.dat', dichroics['bgr-yjhk'][1]._model, dichroics['bgr-yjhk'][0]._model, header=hdr_i)

## Second layer dichroic in BGR arm: U, splits UB from GR
hdr_u = f"""# name : second_layer_dichroic_UBVIS
# author : unknown
# date_created : 2026-03-16T12:00:00
# date_modified : {Time.now().isot}
# description : Transmits GR (VIS) reflects UB
# wavelength_unit : um
# changes :
#"""
write_dichroic_curves(DICHROIC_DIR / 'TER_dichroic_b-gr.dat', dichroics['b-gr'][1]._model, dichroics['b-gr'][0]._model, header=hdr_u)

## Second layer dichroic in YJHK arm: J, splits YJ from HK
hdr_j = f"""# name : second_layer_dichroic_NIR
# author : unknown
# date_created : 2026-03-16T12:00:00
# date_modified : {Time.now().isot}
# description : Transmits HK, reflects YJ
# wavelength_unit : um
# changes :
#"""
write_dichroic_curves(DICHROIC_DIR / 'TER_dichroic_yj-hk.dat', dichroics['yj-hk'][1]._model, dichroics['yj-hk'][0]._model, header=hdr_j)

## Third layer dichroic in GR arm: G, splits G from R
hdr_g = f"""# name : third_layer_dichroic_VIS
# author : unknown
# date_created : 2026-03-16T12:00:00
# date_modified : {Time.now().isot}
# description : Transmits R, reflects G
# wavelength_unit : um
# changes :
#"""
write_dichroic_curves(DICHROIC_DIR / 'TER_dichroic_g-r.dat', dichroics['g-r'][1]._model, dichroics['g-r'][0]._model, header=hdr_g)

## Third layer dichroic in HK arm: H, splits H from K
hdr_h = f"""# name : third_layer_dichroic_HK
# author : unknown
# date_created : 2026-03-16T12:00:00
# date_modified : {Time.now().isot}
# description : Transmits K, reflects H
# wavelength_unit : um
# changes :
#"""
write_dichroic_curves(DICHROIC_DIR / 'TER_dichroic_h-k.dat', dichroics['h-k'][1]._model, dichroics['h-k'][0]._model, header=hdr_h)
