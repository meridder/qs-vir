import os

os.system('rm -rf QSVir_Jan*')

# Splitting off the necessary spectral windows from the untar-ed MS file.
# Spectral windows 0 - 15 were part of a dummy pointing and not needed for analysis.
split(vis='22B-257.sb43147052.eb43156941.59935.54498520833/22B-257.sb43147052.eb43156941.59935.54498520833.ms',outputvis='QSVir_Jan.ms', spw='16~31,32~63,96~127', datacolumn='data')

# The data are now ready for polarization calibration.
