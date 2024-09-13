These scripts will fit the MFS and spectral window images in Stokes I and V as well as find the 3-sigma upper limit on the linear polarization. All are designed to be executed with CASA, but rely on couple other common Python packages. In order to run fit_V.py, fit_sed.py, or lin-pol.py, fit_MFS.py will need to be run first because it produces a position file that is used by the other scripts for forced aperture photometry.