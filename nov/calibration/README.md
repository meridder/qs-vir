These calibration scripts are to be used in the following order:

1. Run the pipeline script, which depends on the list of flags given. Any flags you wish to add can be appended to this file.
2. Run `split_from_ms.py`, which uses the CASA split command to make a new MS file containing only the relevant spectral windows.
3. Run `pol_models.py`, which requires data to be downloaded from the NRAO website (link provided in the script) of the calibrator 3C286. Outputs of this script are already included in the polarization calibration step.
4. Run `pol_cal_script_pipeline.py`, which takes the MS file from step 2 as an input.
5. Optional: Split off a new MS file containing only the QS Vir field. I find this convenient in case the final file is corrupted for any reason in the imaging step. It also takes up much less space than the MS file with every field included.

The data can now be imaged.
