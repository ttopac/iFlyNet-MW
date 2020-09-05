import numpy as np
import matplotlib.pyplot as plt

vel = input ("Enter the vel to plot: ")
aoa = input ("Enter the aoa to plot: ")
# vel = 10
# aoa = 10
downsample_mult = 1700 #1724.1379310344828 means 1 datapoint per second since sampling rate is 1724.1379310344828 for drift test

driftData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/drift1_Sept5/drifttest_{}ms_{}deg.npy'.format(vel,aoa))
# driftData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/drift1_Sept5/drifttest_{}ms_{}deg.npy'.format(vel,aoa))
downsampled_liftSG = np.mean (driftData[14,:].reshape(-1,downsample_mult), axis=1) #Downsample the Lift SG data
downsampled_SG1 = np.mean (driftData[9,:].reshape(-1,downsample_mult), axis=1) #Downsample the SG1 data
xs = np.linspace(0,downsampled_liftSG.shape[0]/60,downsampled_liftSG.shape[0])

fig = plt.figure(figsize=(6.0, 6.0))
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
ax1.set_title("SG Lift for V = {}m/s, AoA = {}deg".format(vel,aoa), fontsize=12)
ax1.set_xlabel("Time (min)", fontsize=11)
ax1.set_ylabel("Microstrain (us)", fontsize=11)
ax2.set_title("SG1 readings for V = {}m/s, AoA = {}deg".format(vel,aoa), fontsize=12)
ax2.set_xlabel("Time (min)", fontsize=11)
ax2.set_ylabel("Voltage (V)", fontsize=11)

ax1.plot(xs, downsampled_liftSG, marker='o')
ax2.plot(xs, downsampled_SG1, marker='o')
plt.tight_layout(pad=2.0)
plt.show()