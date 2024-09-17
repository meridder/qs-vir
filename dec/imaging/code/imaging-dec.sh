#!/bin/bash
#SBATCH --time=6:00:00
#SBATCH --account=your_account
#SBATCH --mem=65G
#SBATCH --cpus-per-task=16
#SBATCH --output=job_output_name
#SBATCH --mail-user=your_email@domain
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL

# This is a script designed to work on a slurm cluster (e.g. Graham/Cedar of the Digital Research Alliance of Canada). 
# You will need a container or multiple containers with WSClean, CubiCal, and breizorro installed in order to use it 
# on another cluster. Otherwise, make sure to install CASA, WSClean, CubiCal, and breizorro and edit the lines that 
# include "apptainer exec" to begin with only the appropriate function.
# If you want to use containers on a cluster, make sure to edit the path to CASA and the path to the container(s) below
# as well as edit the bash preamble above to include your account, email, etc. I've found the memory and cpu requirements
# already above to be sufficient to image all the frequency bands in a few hours.

echo "'''"
cat imaging-dec.sh
echo "'''"

echo 'Loading modules...'
module load StdEnv
module load python
module load apptainer

unset APPTAINER_BIND

echo 'Removing old files...'
rm -rf ../images/* ../ms_files/*.tmp
rm -rf ../CubiCal_output/DI_*
rm -rf ../CubiCal_output/DD_*

echo 'Starting gigantic for loop through all ms files...'
for msfile in ../ms_files/*.ms;do

    echo 'Cleaning $msfile...'

    # Define the image name    
    imname="${msfile/ms_files/images}"
    
    # Determine what cell sizes to use
    # S Band
    if [[ "$msfile" == *"_S"* ]]; then
        channels=16 # set to the number of spectral windows in each band
        imsize=4000
        cellsize='0.97arcsec' # pixel sizes are set at the beam minor axis/5
        subbands=('0~7' '8~15' '16~23' '24~31') # used by CubiCal
        freqint="512"
    fi
    
    # C Band
    if [[ "$msfile" == *"_C"* ]]; then
        channels=32
        imsize=5000
        cellsize='0.49arcsec'
        subbands=('0~7' '8~15' '16~23' '24~31')
        freqint="512"
    fi
    
    # X Band
    if [[ "$msfile" == *"_X"* ]]; then
        channels=32
        imsize=4000
        cellsize='0.31arcsec'
        subbands=('0~15' '15~31')
        freqint="1024"
    fi
 
    # Need to restore the flags for each MS file with CASA before running WSClean.
    xvfb-run /path/to/casa -c restore_flags.py -f $msfile -v pre-selfcal --no-flag # xvfb-run allows CASA to run without needing a display on Graham/Cedar.

    # Making a "dirty" image in Stokes I
    apptainer exec -B /scratch /path/to/wsclean/container wsclean -size $imsize $imsize -scale ${cellsize} -pol I -mgain 0.85 -niter 100000000 -auto-mask 5 -auto-threshold 1 -channels-out ${channels} -fit-spectral-pol 4 -join-channels -name ${imname::-3}_base -data-column DATA -no-update-model-required -weight briggs 0.0 -gridder wgridder -parallel-gridding 16 -no-mf-weighting $msfile

    # Making a mask with the previous image.
    apptainer exec -B /scratch /path/to/breizorro/container breizorro --fill-holes --dilate=1 --boxsize=50 --threshold=6.5 --outfile=${imname::-3}_mask.fits --restored-image=${imname::-3}_base-MFS-image.fits

    # Making pre-self-cal images in Stokes Q, U, V, and I
    apptainer exec -B /scratch /path/to/wsclean/container wsclean -size $imsize $imsize -scale ${cellsize} -pol IQUV -mgain 0.85 -niter 100000000 -auto-mask 3 -auto-threshold 1 -channels-out ${channels} -fit-spectral-pol 4 -join-channels -join-polarizations -name ${imname::-3}_base -data-column DATA -update-model-required -weight briggs 0.0 -gridder wgridder -parallel-gridding 16 -no-mf-weighting -fits-mask ${imname::-3}_mask.fits $msfile
 
    ###############################################
    # Run DI phase-self-calibration using CubiCal #
    ###############################################

    # IMPORTANT: the SNR in the QS Vir field are NOT SUFFICIENT for self-calibration. This should only be used for imaging the calibrators.
    #if [[ "$msfile" == *"_S"* ]] || [[ "$msfile" == *"_C"* ]] || [[ "$msfile" == *"_X"* ]]; then
    #    for i in "${subbands[@]}";do
    #        apptainer exec -B /scratch /path/to/cubical/container gocubical ../parsets/DI_bb.parset --data-ms $msfile --out-dir ../CubiCal_output/DI_bb$i.cc --out-name DI_bb$i --sel-ddid $i --k-freq-int $freqint --data-freq-chunk $freqint
        
    #    done

    # Making post-self-cal images in Stokes Q, U, V, and I
    #apptainer exec -B /scratch /path/to/wsclean/container/ wsclean -size $imsize $imsize -scale ${cellsize} -pol IQUV -mgain 0.85 -niter 10000000 -auto-mask 3 -auto-threshold 1 -channels-out ${channels} -fit-spectral-pol 4 -join-channels -join-polarizations -name ${imname::-3}_scal -data-column CORRECTED_DATA -no-update-model-required -weight briggs 0.0 -gridder wgridder -parallel-gridding 16 -no-mf-weighting -fits-mask ${imname::-3}_mask.fits $msfile
    
    #fi

    # Deleting unnecessary files
    rm ../images/*00*Q* ../images/*00*U*/ ../images/*-dirty* ../images/*-psf* *.log *.last *parmdb*
    
done

# Organizing the images
mkdir ../images/C_images ../images/X_images ../images/S_images
mv ../images/QSVir_S* ../images/S_images/.;mv ../images/QSVir_C* ../images/C_images/.;mv ../images/QSVir_X* ../images/X_images/.
