import os, glob
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

########################################
# Define the parameters of the ms file #
########################################
ms_prefix    = 'QSVir_Jan'
primary_ID   = '1331+305=3C286'
leakage_ID   = 'J1407+2827'
secondary_ID = 'J1351-1449'
source_ID    = 'QS_VIr_Offset'
config       = 'C'
refant       = 'ea05'
last_flag    = 'statwt_1'
#formerly 16~31,32~63,96~127
all_spws     = '0~15,16~47,48~79'
basebands    = ['0~7', '8~15', '16~31', '32~47', '48~63', '64~79']

################################################
# Extracting the Data from the pipeline Output #
################################################

# Copy over the ms file from pipeline directory
#os.system('rm -rf QSVir_Jan*')
os.system('cp -r ../QSVir_Jan/QSVir_Jan.ms .')
os.system('cp -r ../QSVir_Jan/QSVir_Jan.ms.flagversions .')

# Restore the Pre-applycal flags to remove the parangle correction
flagmanager(vis='{}.ms'.format(ms_prefix),mode='restore',versionname=last_flag)

# Apply some manual flagging to correct for some missed flags 
flagdata(vis='{}.ms'.format(ms_prefix), mode='manual', spw='0', flagbackup=False)
flagdata(vis='{}.ms'.format(ms_prefix), mode='manual', spw='4~5', antenna ='ea19', flagbackup=False)
flagdata(vis='{}.ms'.format(ms_prefix), mode='manual', antenna ='ea17', flagbackup=False)
flagdata(vis='{}.ms'.format(ms_prefix), mode='manual', spw='32', antenna ='ea02', flagbackup=False)
#check X band

#################################
# Copy over pipeline cal tables #
#################################

# Initialize arrays to contain calibration parameters
gaintables = [] # Intialize calibration table array
gainfields = [] 
interps = []
spwmaps = []

# Copy the calibration tables from the pipeline
table_name_array = ['hifv_priorcals.s5_2.gc.tbl', 'hifv_priorcals.s5_3.opac.tbl', 'hifv_priorcals.s5_4.rq.tbl', 'hifv_finalcals.s13_2.finaldelay.tbl', 'hifv_finalcals.s13_4.finalBPcal.tbl' ,'hifv_finalcals.s13_5.averagephasegain.tbl', 'hifv_finalcals.s13_7.finalampgaincal.tbl', 'hifv_finalcals.s13_8.finalphasegaincal.tbl']

os.system('rm -r *hifv*')
for table_name in table_name_array:
    os.system('cp -r ../QSVir_Jan/*{} .'.format(table_name))
    hifv = glob.glob('*{}'.format(table_name))[0]
    gaintables.append(hifv)
    gainfields.append('')
    spwmaps.append([])
    if 'finalBPcal' in hifv:
        interps.append('linear,linearflag')
    else:
        interps.append('')

# Re-apply the Stokes I calibration tables after setting parang = False
print('Re-Applying Pipeline Calibration Tables')
applycal(vis='{}.ms'.format(ms_prefix),
         gaintable=gaintables,
         gainfield=gainfields, 
         interp=interps, 
         spwmap=spwmaps, 
         calwt=False, 
         parang=False, 
         applymode='calflagstrict', 
         flagbackup=False)
         
# Apply additional auto-flagging to parrallel hand correlations 
print('Flagging parallel-hand correlations')
flagdata(vis='{}.ms'.format(ms_prefix),
         mode='rflag', correlation='ABS_RR,LL', intent='*CALIBRATE*',
         datacolumn='corrected', ntime='scan', combinescans=False,
         extendflags=False, winsize=3, timedevscale=4.0, freqdevscale=4.0,
         action='apply', flagbackup=False, savepars=False)

flagdata(vis='{}.ms'.format(ms_prefix),
         mode='rflag', correlation='ABS_RR,LL', intent='*TARGET*',
         datacolumn='corrected', ntime='scan', combinescans=False,
         extendflags=False, winsize=3, timedevscale=4.0, freqdevscale=4.0,
         action='apply', flagbackup=False, savepars=False)
         
# Save pre-polcal flags
test=os.path.exists(ms_prefix + '.ms.flagversions/flags.before_polcal')
if test == True:
	flagmanager(vis='{}.ms'.format(ms_prefix), mode='delete', versionname='before_polcal')
flagmanager(vis='{}.ms'.format(ms_prefix),mode='save',versionname='before_polcal')

#####################################
# Flagging the cross-hand solutions #
#####################################
print('Flagging cross-hand correlations')
# Apply auto-flagging to the Cross-hand correlations 
flagdata(vis='{}.ms'.format(ms_prefix),
	 mode='tfcrop',
	 field='{},{},{}'.format(primary_ID, secondary_ID, leakage_ID),
	 correlation='',
	 freqfit='line',
	 extendflags=False,
	 flagbackup=False)

flagdata(vis='{}.ms'.format(ms_prefix),
	 mode='rflag',
	 datacolumn='corrected',
	 field='{},{},{}'.format(primary_ID, secondary_ID, leakage_ID),
	 correlation='RL,LR',
	 extendflags=False,
	 flagbackup=False)
	 
# Save flags after auto-flagging on cross-hand
test=os.path.exists(ms_prefix + '.ms.flagversions/flags.after_cross_autoflag')
if test == True:
	flagmanager(vis='{}.ms'.format(ms_prefix), mode='delete', versionname='after_cross_autoflag')
flagmanager(vis='{}.ms'.format(ms_prefix),mode='save',versionname='after_cross_autoflag') 

#################################
# Define the Polarization Model #
#################################

# Model Coefficients -- extracted using pol_models.py
reffreq='7.0GHz'
flux0=5.810247595591976
alpha = [-0.678287536048642, -0.126889607660176] 
PF_coeffs= [0.11935605390610031, 0.0036576309223830253, -0.01035708606471863, 0.021932951070192726, -0.01030585060318489] 
EVPA_coeffs= [0.5766438867486896, 0.0057019750788444385, 0.01198353059142638, 0.005007155601162313, -0.005059090139551669] 

print('Applying Lin. Pol. Polarization Model')
# Define the polarized model
setjy(vis='{}.ms'.format(ms_prefix),
      field=primary_ID,
      spw='',
      selectdata=False,
      timerange="",
      scan="",
      intent="",
      observation="",
      scalebychan=True,
      standard="manual",
      model="",
      modimage="",
      listmodels=False,
      fluxdensity=[flux0, 0, 0, 0],
      spix=alpha,
      reffreq=reffreq,
      polindex=PF_coeffs,
      polangle=EVPA_coeffs,
      rotmeas=0,
      fluxdict={},
      useephemdir=False,
      interpolation="nearest",
      usescratch=True,
      ismms=False,
)

#####################################
# Solve for Cross-Hand Calibrations #
#####################################

# Solve for Multiband Delay -- we have to do this 1 baseband at a time
# If this doesn't make sense don't worry about it
# Trust the process
print('Solving for Multi-Band Cross-Delay')
kcross = "{}.Kcross".format(ms_prefix) 
for i, baseband in enumerate(basebands):
    bottom_spw, top_spw = np.array(baseband.split('~')).astype(int)
    size = top_spw - bottom_spw + 1
    if i == 0:        
        spwmap = [bottom_spw] * size
        append = False
        
    else:
        spwmap += [bottom_spw] * size 
        append = True
    
    gaincal(vis='{}.ms'.format(ms_prefix),
        caltable=kcross,
        field=primary_ID,
        spw=baseband,
        refant=refant,
        gaintype="KCROSS",
        solint="inf",
        combine="scan,spw",
        calmode="ap",
        gaintable=gaintables,
        gainfield=gainfields,
        interp=interps,
        spwmap=spwmaps,
        append=append,
        parang=True)
   
gaintables.append(kcross)
gainfields.append('')
interps.append('')
spwmaps.append(spwmap)

print('Solving for Leakage')
# Solve for the Leakage solution
Df_leakage = "{}.Df".format(ms_prefix)
polcal(vis='{}.ms'.format(ms_prefix),
    caltable=Df_leakage,
    field=leakage_ID,
    spw=all_spws,
    refant=refant,
    poltype="Df",
    solint="inf,2MHz",
    combine="scan",
    gaintable=gaintables,
    gainfield=gainfields,
    interp=interps,
    spwmap=spwmaps)

gaintables.append(Df_leakage)
gainfields.append('')
interps.append('')
spwmaps.append([])

print('Solving for R-L polarization angle (i.e. Absolute EVPA calibration)')
# Solve for R-L Polarization angle
Xf = "{}.Xf".format(ms_prefix)
polcal(vis='{}.ms'.format(ms_prefix),
    caltable=Xf,
    field=primary_ID,
    spw=all_spws,
    refant=refant,
    poltype="Xf",
    solint="inf,2MHz",
    combine="scan",
    gaintable=gaintables,
    gainfield=gainfields,
    interp=interps,
    spwmap=spwmaps)
    
gaintables.append(Xf)
gainfields.append('')
interps.append('')
spwmaps.append([])

print('Applying New -- Full Pol. Solutions')
# Calibrate the Data
applycal(vis = '{}.ms'.format(ms_prefix),
         field='',
         gainfield=gainfields, 
         flagbackup=True,
         interp=interps,
         gaintable=gaintables,
         spw=all_spws, 
         calwt=False, 
         applymode='calflagstrict',
         spwmap=spwmaps, 
         parang=True)
         
statwt('{}.ms'.format(ms_prefix))

flagmanager(vis='{}.ms'.format(ms_prefix), mode='save', versionname='pre-selfcal')
