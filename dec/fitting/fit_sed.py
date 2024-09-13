import numpy as np
import glob
import os

os.system('rm -rf results-sed*')
#os.system('mv *.log casa-logs/')

# IMPORTANT: fit_MFS.py must be run first! This script takes the position produced
# by fit_MFS.py in order to fit the spectral window images. This script produces a
# text file with the flux, flux error, and frequency information and will delete it
# for consecutive runs. At the bottom of this script, you will need to input the
# directories where you are storing the images.


def fit(image, frequency):

    try:
        # Reading in previous MFS image position in pixel coordinates.
        with open('position-{}I.txt'.format(frequency)) as file:
            pos = [line.rstrip() for line in file]
            file.close()

        ra_pos = pos[0]
        dec_pos = pos[1]

        if 'I-image' in image:
            stoke = 'I'
            # Read some of the image parameters from the header
            freq = imhead(image)['refval'][2]
            bmaj = imhead(image, mode='get', hdkey='bmaj')['value']  # major axis
            bmin = imhead(image, mode='get', hdkey='bmin')['value']  # minor axis
            bpa = imhead(image, mode='get', hdkey='bpa')['value']  # position angle
            source_region = 'circle[[{}pix,{}pix],{}arcsec]'.format(ra_pos, dec_pos, bmaj)

            # Get the maximum postion in pixels and flux of the max pixel using imstat (this doesn't do any fitting it just read pixel values)
            max_pixel = imstat(image, region=source_region)['max'][0]
            # Make an estimate file for fitting, the 'abp', means that we are fixing the shape of the component to the shape of the synthesized beam (it's a point source)
            f = open('estimate.txt', 'w')
            f.write('{},{},{},{}arcsec,{}arcsec,{}deg, xyabp'.format(max_pixel, ra_pos, dec_pos, bmaj, bmin, bpa))
            f.close()

        if 'V-image' in image:
            stoke = 'V'
            # Read in position estimate from last I image as a list.
            try:
                freq = imhead(image)['refval'][2]
                bmaj = imhead(image, mode='get', hdkey='bmaj')['value']  # major axis
                bmin = imhead(image, mode='get', hdkey='bmin')['value']  # minor axisw
                bpa = imhead(image, mode='get', hdkey='bpa')['value']  # position angle
                source_region = 'circle[[{}pix,{}pix],{}arcsec]'.format(ra_pos, dec_pos, bmaj)

                #ra_pixel = pos[0]
                #dec_pixel = pos[1]

                f = open('estimate.txt', 'w')
                f.write('0,{},{},{}arcsec,{}arcsec,{}deg, xyabp'.format(ra_pos, dec_pos, bmaj, bmin, bpa))
                f.close()
            except FileNotFoundError:
                print('Previous Stokes I fit unsuccessful. Skipping to next file.')

        # Fit the component get the flux and the positions
        fit = imfit(image, region=source_region, estimates='estimate.txt')

        flux = fit['results']['component0']['peak']['value']  # in Jy
        ra = fit['results']['component0']['shape']['direction']['m0']['value'] * 180.0 / np.pi  # in degrees
        dec = fit['results']['component0']['shape']['direction']['m1']['value'] * 180.0 / np.pi
 
        if ra < 0:
            ra += 360

        # Solve for the RMS region, it will have an area of ~100 beams
        area = np.pi * bmaj ** 2
        annulus_area = 100 * area
        inner_radius = bmaj
        outer_radius = np.sqrt((annulus_area + area) / np.pi)
        annulus = 'annulus[[{}deg,{}deg],[{}arcsec,{}arcsec]]'.format(ra, dec, inner_radius, outer_radius)

        # Get rms using the annulus region
        rms = imstat(image, region=annulus)['rms'][0]

        # Solve for the accuracy of the centroiding using the SNR of the detection: https://math.stackexchange.com/questions/91132/how-to-get-the-limits-of-rotated-ellipse
        ra_ext = 2 * np.sqrt((bmaj / 2) ** 2 * np.cos(bpa * 180.0 / np.pi) ** 2 + (bmin / 2) ** 2 * np.sin(
            bpa * 180.0 / np.pi) ** 2) / 3600.0  # in arcseconds
        dec_ext = 2 * np.sqrt((bmaj / 2) ** 2 * np.sin(bpa * 180.0 / np.pi) ** 2 + (bmin / 2) ** 2 * np.cos(
            bpa * 180.0 / np.pi) ** 2) / 3600.0  # in arcseconds
        snr = flux / rms

        ra_err = np.sqrt((ra_ext / (2 * snr)) ** 2 + (ra_ext / (10)) ** 2)
        dec_err = np.sqrt((dec_ext / (2 * snr)) ** 2 + (dec_ext / (10)) ** 2)
        # print(ra_err * 3600.0, dec_err * 3600)

        # ra_err = ra_ext/(2 * snr)
        # dec_err = dec_ext/(2 * snr)

        print('flux = {} +/- {} muJy, RA = {} +/- {}deg, Dec = {} +/- {}deg'.format(flux * 1e6, rms * 1e6, ra, ra_err,
                                                                                    dec, dec_err))

        res = open('results-sed-{}-{}.txt'.format(frequency, stoke), 'a')
        res.write('{},{},{}\n'.format(flux * 1e6, rms * 1e6, freq))
        res.close()

    except KeyError:
        print('Fit failed.')
    except TypeError:
        print('Fit failed. File may consist of flagged spectral windows (NaNs).')
    except UnboundLocalError:
        print('Resuming shortly...')


# I must be run before V, both arrays are of the same length

SI = np.sort(glob.glob('path/to/S/images/*-0*I*image.fits'))
SV = np.sort(glob.glob('path/to/S/images/*-0*V-image.fits'))
for i in range(len(SI)):
    print('\n', SI[i])
    fit(SI[i], 'S')
    print(SV[i])
    fit(SV[i], 'S')

CI = np.sort(glob.glob('path/to/C/images/*-0*I-image.fits'))
CV = np.sort(glob.glob('path/to/C/images/*-0*V-image.fits'))
for i in range(len(CI)):
    print('\n', CI[i])
    fit(CI[i], 'C')
    print(CV[i])
    fit(CV[i], 'C')

XI = np.sort(glob.glob('path/to/X/images/*-0*I-image.fits'))
XV = np.sort(glob.glob('path/to/X/images/*-0*V-image.fits'))
for i in range(len(XI)):
    print('\n', XI[i])
    fit(XI[i], 'X')
    print(XV[i])
    fit(XV[i], 'X')
