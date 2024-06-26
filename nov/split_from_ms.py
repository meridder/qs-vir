import os

os.system('rm -rf QSVir_Nov*')

split(vis='/arc/projects/QS-Vir-VLA/22B-257.sb42746926.eb43026151.59911.619846851856/22B-257.sb42746926.eb43026151.59911.619846851856.ms',
outputvis='QSVir_Nov.ms', spw='16~31,32~63,124~155', datacolumn='data')

os.system('mv *.log casa-logs')
