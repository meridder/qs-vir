import numpy as np
import glob
import os

# IMPORTANT: fit_MFS.py must be run first! This script takes the position file
# produced by fit_MFS.py in order to fit the Stokes V images. This script produces
# one text file containing the flux, flux error, and frequency information and
# deletes this file for consequtive runs. This file does not need to be run before
# fit_sed.py. At the bottom of this script, you will need to input the path to the
# directories where you are storing the images.

os.system('rm results-MFS*V*.txt')

def fit(image_name, frequency):
    try:
        with open('position-{}I.txt'.format(frequency)) as file:
            pos = [line.rstrip() for line in file]
            file.close()

        ra_pos = pos[0]
        dec_pos = pos[1]

        # Read some of the image parameters from the header
        freq = imhead(image_name)['refval'][2]
        bmaj = imhead(image_name, mode='get', hdkey='bmaj')['value']  # major axis
        bmin = imhead(image_name, mode='get', hdkey='bmin')['value']  # minor axis
        bpa = imhead(image_name, mode='get', hdkey='bpa')['value']  # position angle
        source_region = 'circle[[{}pix,{}pix],{}arcsec]'.format(ra_pos, dec_pos, bmaj)

        # Get the maximum postion in pixels and flux of the max pixel using imstat (this doesn't do any fitting it just
        # read pixel values)
        min_pixel = imstat(image_name, region=source_region)['min'][0]
        # Make an estimate file for fitting, the 'abp', means that we are fixing the shape of the component to the shape of
        # the synthesized beam (it's a point source)
        f = open('estimate.txt', 'w')
        f.write('{},{},{},{}arcsec,{}arcsec,{}deg, xyabp'.format(min_pixel, ra_pos, dec_pos, bmaj, bmin, bpa))
        f.close()

        # Fit the component get the flux and the positions
        fit = imfit(image_name, region=source_region, estimates='estimate.txt')
        flux = fit['results']['component0']['peak']['value']  # in Jy
        ra = fit['results']['component0']['shape']['direction']['m0']['value'] * 180.0 / np.pi  # in degrees
        dec = fit['results']['component0']['shape']['direction']['m1']['value'] * 180.0 / np.pi

        if ra < 0:
            ra += 360

        # Solve for the RMS region, it will have an area of ~100 beams
        area = np.pi * bmaj ** 2
        annulus_area = 100 * area
        inner_radius = 0.75 * bmaj
        outer_radius = np.sqrt((annulus_area + area) / np.pi)
        annulus = 'annulus[[{}deg,{}deg],[{}arcsec,{}arcsec]]'.format(ra, dec, inner_radius, outer_radius)

        # Get rms using the annulus region
        rms = imstat(image_name, region=annulus)['rms'][0]

        # Solve for the accuracy of the centroiding using the SNR of the detection:
        # https://math.stackexchange.com/questions/91132/how-to-get-the-limits-of-rotated-ellipse
        ra_ext = 2 * np.sqrt((bmaj / 2) ** 2 * np.cos(bpa * 180.0 / np.pi) ** 2 + (bmin / 2) ** 2 * np.sin(
            bpa * 180.0 / np.pi) ** 2) / 3600.0  # in arcseconds
        dec_ext = 2 * np.sqrt((bmaj / 2) ** 2 * np.sin(bpa * 180.0 / np.pi) ** 2 + (bmin / 2) ** 2 * np.cos(
            bpa * 180.0 / np.pi) ** 2) / 3600.0  # in arcseconds
        snr = flux / rms
        ra_err = np.sqrt((ra_ext / (2 * snr)) ** 2 + (ra_ext / 10) ** 2)
        dec_err = np.sqrt((dec_ext / (2 * snr)) ** 2 + (dec_ext / 10) ** 2)

        print('flux = {} +/- {} muJy, RA = {} +/- {}deg, Dec = {} +/- {}deg'.format(flux * 1e6, rms * 1e6, ra,
                                                                                    ra_err, dec, dec_err))
        res = open('results-MFS-{}V.txt'.format(frequency), 'a')
        res.write('{},{},{}\n'.format(flux * 1e6, rms * 1e6, freq))
        res.close()

    except KeyError:
        print('Fit failed.')
    except TypeError:
        print('Fit failed.')


# Reading in all files
S = np.sort(glob.glob('path/to/S/images/*MFS*V-image.fits'))
C = np.sort(glob.glob('path/to/C/images/*MFS*V-image.fits'))
X = np.sort(glob.glob('path/to/X/images/*MFS*V-image.fits'))

for i in range(len(S)):
    print('\n', S[i])
    fit(S[i], 'S')

for i in range(len(C)):
    print('\n', C[i])
    fit(C[i], 'C')

for i in range(len(X)):
    print('\n', X[i])
    fit(X[i], 'X')
