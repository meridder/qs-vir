import os

os.system('rm -rf QSVir_Nov*')

# Splitting off the necessary spectral windows from the untar-ed MS file.
# Spectral windows 0 - 15 were part of a dummy pointing and not needed for analysis. Note that two of the 
# spectral windows in the first subband of C are missing and the spectral windows in X are out of order in this epoch.
# The numbers included select only the necessary data. Keep in mind that unordered spectral windows may create
# problems with self-calibration if you choose to use it (not recommended due to low SNR).
split(vis='22B-257.sb42746926.eb43026151.59911.619846851856/22B-257.sb42746926.eb43026151.59911.619846851856.ms',
outputvis='QSVir_Nov.ms', spw='16~31,32~63,124~155', datacolumn='data')
