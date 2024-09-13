import numpy as np
import os
import glob

# IMPORTANT: This must be run after fit_MFS.py! This script takes the position file
# produced by fit_MFS.py in order to find the right region to fit. Rather than fitting
# a 2D Gaussian, this script produces the 3-sigma upper limit on the flux since no
# linear polarization was observed above the noise. This script computes the total
# linear polarization from Stokes Q and U images. Below, you will need to edit the path
# names to point to the directories where you are storing these images.

os.system('rm -rf *-linpol')

bands = ['S', 'C', 'X']

for b in bands:
    files = glob.glob('path/to/Q/and/U/images/*_{}_*MFS*image.fits'.format(b))
    print(files)

    with open('/path/to/position-{}I.txt'.format(b)) as file:
        pos = [line.rstrip() for line in file]
        file.close()

    # Getting beam size/shape
    bmaj = imhead(files[0], mode='get', hdkey='bmaj')['value']
    beam_area = np.pi * bmaj ** 2
    rmsfit_area = 100 * beam_area
    radius = np.sqrt(rmsfit_area / np.pi)
    source_region = 'circle[[{}pix,{}pix], {}arcsec]'.format(pos[0], pos[1], radius)

    # Making lin pol image from Q and U
    immath(imagename=[files[0], files[1]], outfile='{}-linpol'.format(b), mode='poli')

    # Finding RMS of the region (there were no detections)
    rms = imstat('{}-linpol'.format(b), region=source_region)['rms'][0] * 1e6

    print('3 x RMS upper limit: {} muJy'.format(rms * 3))

#os.system('mv *.log casa-logs/')

