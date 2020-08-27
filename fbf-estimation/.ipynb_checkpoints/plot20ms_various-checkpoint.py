import numpy as np
import matplotlib.pyplot as plt
import os
import process_utils

#%% Plot unfiltered Labview data from earlier.
LWdirectory = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/Test Data/Raw Data/'

# We will plot 20m/s data at 2degrees, 18 degrees, and 20 degrees
#Import raw Labview data as Numpy array and plot them
LW_2deg = process_utils.convert_to_np_labview_single(LWdirectory+'03.30 20m s ★/txt/Airspeed20_AOA2.txt',sensor='PZTLB')
LW_18deg = process_utils.convert_to_np_labview_single(LWdirectory+'03.30 20m s ★/txt/Airspeed20_AOA18.txt',sensor='PZTLB')
LW_20deg = process_utils.convert_to_np_labview_single(LWdirectory+'03.30 20m s ★/txt/Airspeed20_AOA20.txt',sensor='PZTLB')

plt.plot(LW_2deg[70,:])
plt.plot(LW_18deg[70,:])
plt.plot(LW_20deg[70,:])
plt.legend(['2deg','18deg','20deg'])
plt.show()


#%% Plot numpy data
NPdirectory = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/FreqTest/'

# Plot 20m/s_2deg and 20m/s_20deg data captured at 7142 sampling rate
NP_2deg = np.load(NPdirectory+'714285714_20ms_2deg.npy')
NP_20deg = np.load(NPdirectory+'714285714_20ms_20deg.npy')

plt.plot(NP_2deg[2,5000:6000])
plt.plot(NP_20deg[2,5000:6000])
plt.legend(['2deg','20deg'])
plt.show()

#%% Plot filtered data from earlier.
datdirectory = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/Test Data/Neural Network/X1.dat/'

# We will plot 20m/s data at 2degrees, 18 degrees, and 20 degrees
# Import .dat file as Numpy array and plot them
LW_2deg = process_utils.convert_to_np_dat(datdirectory+'PZTRB_20ms_2deg.dat')
LW_18deg = process_utils.convert_to_np_dat(datdirectory+'PZTRB_20ms_18deg.dat')
LW_20deg = process_utils.convert_to_np_dat(datdirectory+'PZTRB_20ms_20deg.dat')

plt.plot(LW_2deg[70,:])
plt.plot(LW_18deg[70,:])
plt.plot(LW_20deg[70,:])
plt.legend(['2deg','18deg','20deg'])
plt.show()