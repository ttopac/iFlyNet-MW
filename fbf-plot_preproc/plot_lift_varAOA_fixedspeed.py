import numpy as np
import matplotlib.pyplot as plt

ave_lift = list()
ave_root_SG = list()

# vel = input ("Enter the vel to plot: ")
# aoa = input ("Enter the aoa to plot: ")
vel = 14
aoa = [0,2,4,6,8,10,12,14,16,17,18,19,20]

for a in aoa:
  # trainData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/')
  trainData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/train1_Sept4/train_{}ms_{}deg.npy'.format(vel,a))
  ave_lift.append(np.mean(trainData[14])) #14 is Lift CommSG
  ave_root_SG.append(np.mean(-1*trainData[6])) #6 is SG1 at root.

fig = plt.figure(figsize=(6.0, 6.0))
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
ax1.set_title("SG Lift for V = {}m/s".format(vel), fontsize=12)
ax1.set_xlabel("Angle (deg)", fontsize=11)
ax1.set_ylabel("Strain (%)", fontsize=11)
ax2.set_title("SG1 readings for V = {}m/s".format(vel), fontsize=12)
ax2.set_xlabel("Angle (deg)", fontsize=11)
ax2.set_ylabel("Voltage (V)", fontsize=11)

ax1.plot(aoa, ave_lift, marker='o')
ax2.plot(aoa, ave_root_SG, marker='o')
plt.tight_layout(pad=2.0)
plt.show()