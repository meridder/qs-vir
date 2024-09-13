import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# Load in the 2019 data from: https://science.nrao.edu/facilities/vla/docs/manuals/obsguide/modes/pol
data = np.loadtxt('3C286_model.txt')

# Separate the columns
freqGHz  = data[:,0]
flux     = data[:,1]
PF       = data[:,2] # Polarization fraction
EVPA     = data[:,3] # Electric Vector Position Angle

# Specify the indexes corresponding to the frequency range of interest
# I recommend you chose your bandwidth +/- (atleast) 1 GHz at either end for padding 
index = np.where((0.0 < freqGHz) & (freqGHz < 18.0))
print('frequenceis (GHz): ', freqGHz[index])

# Truncate columns
freqGHz  = freqGHz[index]
flux     = flux[index]
PF       = PF[index]
EVPA     = EVPA[index]
freq0GHz = 7.0 # reference frequency should be in middle of the band

# Define the fit funtions with freqGHz inputs
def flux_fit(freqGHz, flux0, c0, c1):
        return flux0*(freqGHz/freq0GHz)**(c0+c1*np.log10(freqGHz/freq0GHz))
  
def PF_fit(freqGHz,c0, c1, c2, c3, c4):
        return c0 + c1 * ((freqGHz-freq0GHz)/freq0GHz) + c2 * ((freqGHz-freq0GHz)/freq0GHz)**2 + c3 * ((freqGHz-freq0GHz)/freq0GHz)**3 + c4 * ((freqGHz-freq0GHz)/freq0GHz)**4
        
def EVPA_fit(freqGHz,c0, c1, c2, c3, c4):
        return c0 + c1 * ((freqGHz-freq0GHz)/freq0GHz) + c2 * ((freqGHz-freq0GHz)/freq0GHz)**2 + c3 * ((freqGHz-freq0GHz)/freq0GHz)**3 + c4 * ((freqGHz-freq0GHz)/freq0GHz)**4

# Fit model parameters
flux_coeffs, flux_cov = curve_fit(flux_fit, freqGHz, flux)
PF_coeffs, PF_cov     = curve_fit(PF_fit, freqGHz, PF)
EVPA_coeffs, EVPA_cov = curve_fit(EVPA_fit, freqGHz, EVPA)

# Plot model parameters
freqMod = np.linspace(freqGHz[0], freqGHz[-1], 100000)
fig, ax = plt.subplots(3, figsize=(12,12), sharex=True)
ax[0].scatter(freqGHz, flux)
ax[0].plot(freqMod, flux_fit(freqMod, *flux_coeffs))
ax[0].set_ylabel('Stokes I Flux Density (Jy)')

ax[1].scatter(freqGHz, PF * 100)
ax[1].plot(freqMod, PF_fit(freqMod, *PF_coeffs) * 100)
ax[1].set_ylabel('Polarization Fraction (%)')

ax[2].scatter(freqGHz, np.degrees(EVPA))
ax[2].plot(freqMod, np.degrees(EVPA_fit(freqMod, *EVPA_coeffs)))
ax[2].set_ylabel('Electric Vector Position Angle (deg)')

ax[-1].set_xlabel('Frequency (GHz)')
plt.savefig('model_fits.png')

# Print the Model Parameters
print("reffreq='{}GHz'\nflux0={}".format(freq0GHz,flux_coeffs[0]))
print('alpha =', flux_coeffs[1:].tolist(), '\nPF_coeffs=',PF_coeffs.tolist(), '\nEVPA_coeffs=',EVPA_coeffs.tolist(),'\n')


