#!/bin/bash
#SBATCH --time=6:00:00
#SBATCH --account=def-heinke
#SBATCH --mem=65G
#SBATCH --cpus-per-task=16
#SBATCH --output=polkat_250624_%j
#SBATCH --mail-user=mridder@ualberta.ca
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL

# Will be running  on data calibrated data with new version of CASA. FIRST: old data needs to be saved. Creating MFS images with 16 channels in S band and 32 channels in C/X band.

echo "'''"
cat imaging.sh
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
        channels=16
        imsize=2480
        cellsize='0.97arcsec'
        subbands=('0~7') # only first half for self cal
        freqint="512"
    fi
    
    # C Band
    if [[ "$msfile" == *"_C"* ]]; then
        channels=32
        imsize=5000
        cellsize='0.48arcsec'
        #subbands=('0~7' '8~15' '16~23' '24~31')
        freqint="512"
    fi
    
    # X Band
    if [[ "$msfile" == *"_X"* ]]; then
        channels=32
        imsize=6000
        cellsize='0.32arcsec'
        #subbands=('0~15' '15~31') # no self cal on X band
        freqint="1024"
    fi
   
    #rm -r $msfile ; cp -r ${msfile}_backup ${msfile}
    
    xvfb-run /home/mridder/projects/def-heinke/mridder/CASA/casa-6.5.4-9-pipeline-2023.1.0.124/bin/casa -c restore_flags.py -f $msfile -v pre-selfcal --no-flag

    apptainer exec -B /scratch /project/def-heinke/mridder/qsvir/polkat-0.0.2.sif wsclean -size $imsize $imsize -scale ${cellsize} -pol I -mgain 0.85 -niter 100000000 -auto-mask 5 -auto-threshold 1 -channels-out ${channels} -fit-spectral-pol 4 -join-channels -name ${imname::-3}_base -data-column DATA -no-update-model-required -weight briggs 0.0 -gridder wgridder -parallel-gridding 16 -no-mf-weighting $msfile

    apptainer exec -B /scratch /project/def-heinke/mridder/qsvir/polkat-0.0.2.sif breizorro --fill-holes --dilate=1 --boxsize=50 --threshold=6.5 --outfile=${imname::-3}_mask.fits --restored-image=${imname::-3}_base-MFS-image.fits
    
    apptainer exec -B /scratch /project/def-heinke/mridder/qsvir/polkat-0.0.2.sif wsclean -size $imsize $imsize -scale ${cellsize} -pol IQUV -mgain 0.85 -niter 100000000 -auto-mask 3 -auto-threshold 1 -channels-out ${channels} -fit-spectral-pol 4 -join-channels -join-polarizations -name ${imname::-3}_base -data-column DATA -update-model-required -weight briggs 0.0 -gridder wgridder -parallel-gridding 16 -no-mf-weighting -fits-mask ${imname::-3}_mask.fits $msfile
 
    ###############################################
    # Run DI phase-self-calibration using CubiCal #
    ###############################################
    
    if [[ "$msfile" == *"_S"* ]]; then
        for i in "${subbands[@]}";do
            apptainer exec -B /scratch /project/def-heinke/mridder/qsvir/wbc.sif gocubical ../parsets/DI_bb.parset --data-ms $msfile --out-dir ../CubiCal_output/DI_bb$i.cc --out-name DI_bb$i --sel-ddid $i --k-freq-int $freqint --data-freq-chunk $freqint
        
        done
    
    apptainer exec -B /scratch /project/def-heinke/mridder/qsvir/polkat-0.0.2.sif wsclean -size $imsize $imsize -scale ${cellsize} -pol IQUV -mgain 0.85 -niter 10000000 -auto-mask 3 -auto-threshold 1 -channels-out ${channels} -fit-spectral-pol 4 -join-channels -join-polarizations -name ${imname::-3}_scal -data-column CORRECTED_DATA -no-update-model-required -weight briggs 0.0 -gridder wgridder -parallel-gridding 16 -no-mf-weighting -fits-mask ${imname::-3}_mask.fits $msfile
    
    fi
    
    rm ../images/*00*Q* ../images/*00*U*/ ../images/*-dirty* ../images/*-psf* *.log *.last *parmdb*
    
done

mkdir ../images/C_images ../images/X_images ../images/S_images
mv ../images/QSVir_S* ../images/S_images/.;mv ../images/QSVir_C* ../images/C_images/.;mv ../images/QSVir_X* ../images/X_images/.
