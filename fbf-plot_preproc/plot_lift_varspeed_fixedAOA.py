import numpy as np
import matplotlib.pyplot as plt

ave_lift = list()
ave_root_SG = list()

# vel = input ("Enter the vel to plot: ")
# aoa = input ("Enter the aoa to plot: ")
vel = [2,4,6,8,10,12,14,16,18,20]
aoa = 6

for v in vel:
  # trainData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/')
  trainData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/train1_Sept4/train_{}ms_{}deg.npy'.format(v,aoa))
  ave_lift.append(np.mean(trainData[14])) #14 is Lift CommSG
  ave_root_SG.append(np.mean(-trainData[6])) #6 is SG1 at root.

fig = plt.figure(figsize=(6.0, 6.0))
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
ax1.set_title("SG Lift for AoA = {}deg".format(aoa), fontsize=12)
ax1.set_xlabel("Velocity (m/s)", fontsize=11)
ax1.set_ylabel("Strain (%)", fontsize=11)
ax2.set_title("-SG1 readings for AoA = {}deg".format(aoa), fontsize=12)
ax2.set_xlabel("Velocity (m/s)", fontsize=11)
ax2.set_ylabel("Voltage (V)", fontsize=11)

#Add post-experiment datapoint:
vel.append(0)
postExpData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/train1_Sept4/train_0postms_0postdeg.npy')
ave_lift.append(np.mean(postExpData[14])) #14 is Lift CommSG
ave_root_SG.append(np.mean(-1*postExpData[6])) #6 is SG1 at root.

ax1.plot(vel[0:-1], ave_lift[0:-1], marker='o')
ax1.plot(vel[-1], ave_lift[-1], 'r*')
ax2.plot(vel[0:-1], ave_root_SG[0:-1], marker='o')
ax2.plot(vel[-1], ave_root_SG[-1], 'r*')
plt.tight_layout(pad=2.0)
plt.show()