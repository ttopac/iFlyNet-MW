#This script assumes data starting at zero strain and changing with temperature.
#Both temperature and one commSG data should be provided.

#%%
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import sys, os
from scipy import signal

#%%
vel = '0'
aoa = '0'
test_folder = 'tempcal1_Sept18'
visible_duration = 10 #(minutes) duration of temptest
downsample_mult = 1700 #1700 is close to 1 datapoint per second since sampling rate is 1724.1379310344828 for drift test
# testData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/tempcal_{}ms_{}deg.npy'.format(test_folder,vel,aoa))
testData = np.load('/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/Training_Tests/{}/tempcal_{}ms_{}deg.npy'.format(test_folder,vel,aoa))
commSGdata = testData[15,0:299200]
tempdata = testData[16,0:299200]

#%%
poly_coeffs = np.polyfit(tempdata, commSGdata, 3)
poly = np.poly1d(poly_coeffs)
polycurve = poly(tempdata)

#%% Downsample the data and prepare X-axis for plotting
downsampled_commSGdata = np.mean (commSGdata.reshape(-1,downsample_mult), axis=1)
downsampled_tempdata = np.mean (tempdata.reshape(-1,downsample_mult), axis=1)
downsampled_polycurve = np.mean (polycurve.reshape(-1,downsample_mult), axis=1)
xs = np.linspace(0,visible_duration,downsampled_commSGdata.shape[0]) 

# %%
fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
ax1.plot(xs, downsampled_tempdata, 'r', linewidth='1.0', label="Temperature")
ax1.plot(xs, downsampled_commSGdata, 'b', linewidth='0.5', label="Raw commSG")
ax1.plot(xs, downsampled_polycurve, 'r', ':', linewidth='0.5', label="Temperature Fit")
ax1.legend(fontsize=7, loc="lower right", ncol=1, columnspacing=1)
plt.show()
# %%
print (poly)
# %%