This repository contains the scripts necessary to calibrate and image VLA observations of QS Vir along with scripts to recreate the plots in Ridder et al. (in prep). The data can be obtained from nrao.archive.edu.

The structure of the files in this repository are organized by the month of the observation. Under each of the above directories is a directory for imaging and another for calibration. Steps 1 - 5 correspond to the scripts in under calibration/ and step 6 corresponds to the scripts under imaging/.

The general procedure for producing images from this dataset are as follows:
1. Download the following prerequisites: [WSClean](https://wsclean.readthedocs.io/), [CubiCal](https://cubical.readthedocs.io/), and [breizorro](https://github.com/ratt-ru/breizorro).
2. Download the MS files for all three epochs from the NRAO archive.
3. Split the MS files to include only the necessary spectral windows (epoch-specific, script provided).
4. Run the [CASA](https://casadocs.readthedocs.io/) 6.4.1-12 pipeline script with the epoch-specific flag files.
5. Run the linear polarization calibration script on each epoch.
6. Split the MS files to include only the QS Vir field and separate them into S, C, and X band.
7. Run the imaging script.
