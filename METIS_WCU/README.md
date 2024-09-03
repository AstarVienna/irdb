# METIS WCU

Independent of the implementation options discussed below it may be necessary to move some parameter settings around. For instance, pixel scale is defined top-level in `METIS_IMG_N.yaml` (used in all implementations). It is not clear that this pixel scale is the same for WCU observations or whether it is at all a useful (or necessary) quantity.

## Implementation

Upstream of the METIS CFO, calibration observations use a different
OpticalTrain than science observations. The atmosphere and the ELT are
switched off, instead effects related to the optics of the WCU and the
relay are needed.  Here, we attempt to implement this as a separate
instrument package built on top of the usual METIS
package. `METIS_WCU/default.yaml` defines the same modes as
`METIS/default.yaml`. Instead of importing the ELT and Armazones
packages (or the respective yaml files), it imports `METIS_WCU.yaml`
before handing over to `METIS/METIS.yaml` and the respective mode
yamls.

The simulation is then built as follows:
```
cmds = sim.UserCommands(use_instrument="METIS_WCU", set_modes=["img_lm"])
metis = sim.OpticalTrain(cmds)
```

## Alternative implementation 1

With some rearrangement, `METIS/default.yaml` could define wcu modes in addition to the on-sky modes. In this case, each mode would need to define all necessary yamls, with no yamls being imported on the top level. For instance:
```
- name: img_lm
  yamls:
    - Armazones.yaml
    - ELT.yaml
    - METIS.yaml
    - METIS_IMG_LMS.yaml
    - METIS_DET_IMG_LM.yaml

- name: wcu_img_lm
  yamls:
    - METIS_WCU.yaml
    - METIS.yaml
    - METIS_IMG_LM.yaml
    - METIS_DET_IMG_LM.yaml
```
This results in a long list of modes in a single file, although the total number of modes to be defined is the same as in the current implementation, where it is spread over two files (and two packages). This solution is backwards compatible as the existing modes are unchanged from the user perspective.

In addition to the list of yamls, each mode definition includes a list of `properties`. There will be duplication both in this alternative and in the current implementation, but with the possibility of choosing different values for on-sky and wcu simulations if that is useful.

## Alternative implementation 2

MICADO uses the fact that `set_modes` accepts a list to combine each of the instrument modes with either SCAO or MCAO, e.g. `set_modes=['MCAO', 'IMG_4mas']`. There is no default for the AO mode alone (the implicit default is "no AO"), so both modes must be provided. For METIS, one could use
```
cmds1 = sim.UserCommands(use_instrument="METIS", set_modes=["ELT", "img_lm"])
cmds2 = sim.UserCommands(use_instrument="METIS", set_modes=["WCU", "img_lm"])
```
The mode definitions would then look like this:
```
- name: ELT
  yamls:
    - Armazones.yaml
    - ELT.yaml

- name: WCU
  yamls:
    - METIS_WCU.yaml
```
This increases the number of modes to be defined in `default.yaml` by only two. However, the user interface, requiring explicit specification of `ELT` seems a little awkward (and not backwards compatible).
There is no way to set different `properties` settings for on-sky and wcu observations.


## WCU effects

So far, only a `PupilTransmission` effect has been implemented, to represent the WCU flux controlling masks (E-REP-UZK-MET-1008, Sect. 3.3.2). In reality, this is a wheel with 16 fixed positions. The current effect is controlled by a float parameter, `transmission`, which can be changed with the (undocumented) method `update_transmission`.
