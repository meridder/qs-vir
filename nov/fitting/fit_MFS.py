import numpy as np
import glob
import os

# IMPORTANT: This script must always be run first. It is designed to fit the multi-frequency
# synthesis (MFS) Stokes I images produced by WSClean. The script produces two files that it will
# delete before running multiple times. The first contains the flux, flux error, and frequency
# information. The second contains the position of the source that will be used to fit the
# Stokes V MFS images and spectral window images. You will need to include the path to the
# directory where you are storing the images at the very bottom of this file.

os.system('rm results-MFS*.txt')

def fit(image_name, ra_pos, dec_pos, frequency):
	try:
	        # Read some of the image parameters from the header.
		freq = imhead(image_name)['refval'][2]
		bmaj = imhead(image_name, mode='get', hdkey='bmaj')['value']  # major axis
		bmin = imhead(image_name, mode='get', hdkey='bmin')['value']  # minor axis
		bpa = imhead(image_name, mode='get', hdkey='bpa')['value']  # position angle
		source_region = 'circle[[{}deg,{}deg],{}arcsec]'.format(ra_pos, dec_pos, bmaj)

		# Get the maximum postion in pixels and flux of the max pixel using imstat (this doesn't do any fitting it just
		# read pixel values)
		ra_pixel = imstat(image_name, region=source_region)['maxpos'][0]
		dec_pixel = imstat(image_name, region=source_region)['maxpos'][1]
		max_pixel = imstat(image_name, region=source_region)['max'][0]
		# Make an estimate file for fitting, the 'abp', means that we are fixing the shape of the component to the shape of
		# the synthesized beam (it's a point source)
		f = open('estimate.txt', 'w')
		f.write('{},{},{},{}arcsec,{}arcsec,{}deg, abp'.format(max_pixel, ra_pixel, dec_pixel, bmaj, bmin, bpa))
		f.close()

		# Fit the component get the flux and the positions
		fit = imfit(image_name, region=source_region, estimates='estimate.txt')
		flux = fit['results']['component0']['peak']['value']  # in Jy
		ra = fit['results']['component0']['shape']['direction']['m0']['value'] * 180.0 / np.pi  # in degrees
		dec = fit['results']['component0']['shape']['direction']['m1']['value'] * 180.0 / np.pi
		s = open('position-{}I.txt'.format(frequency), 'w')
		s.write('{}\n{}'.format(fit['results']['component0']['pixelcoords'][0],
								fit['results']['component0']['pixelcoords'][1]))
		s.close()

		if ra < 0:
			ra += 360

		# Solve for the RMS region, it will have an area of ~100 beams
		area = np.pi * bmaj ** 2
		annulus_area = 100 * area
		inner_radius = bmaj
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
		res = open('results-MFS{}.txt'.format(frequency), 'a')
		res.write('{},{},{}\n'.format(flux * 1e6, rms * 1e6, freq))
		res.close()

	except KeyError:
		print('Fit failed.')
	except TypeError:
		print('Fit failed.')


# Reading in all files
S = np.sort(glob.glob('path/to/S/images/*MFS*I-image.fits'))
C = np.sort(glob.glob('path/to/C/images/*MFS*I-image.fits'))
X = np.sort(glob.glob('path/to/X/images/*MFS*I-image.fits'))

for i in range(len(S)):
	print('\n',S[i])
	fit(S[i], '207.466870', '-13.226865', 'S')

for i in range(len(C)):
	print('\n',C[i])
	fit(C[i], '207.466870', '-13.226865', 'C')

for i in range(len(X)):
	print('\n',X[i])
	fit(X[i], '207.466870', '-13.226865', 'X')

