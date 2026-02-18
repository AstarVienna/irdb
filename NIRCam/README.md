# NIRCam @ JWST

## PSFs
The PSFs are provided per filter. The current version of this package uses the
PSFs from the broadband filters as a "good enough" solution for all short and
long wavelength filters, respectively. In both cases, the "DET_SAMP" extension
was used, which is the one _without_ added distortions (which are reported to be
low anyway for center-of-field), sampled to the detector pixel resolution.

## Links to resources

https://jwst-docs.stsci.edu/jwst-near-infrared-camera/nircam-instrumentation/nircam-detector-overview/nircam-detector-performance#gsc.tab=0

https://stsci.app.box.com/v/jwst-simulated-psf-library
