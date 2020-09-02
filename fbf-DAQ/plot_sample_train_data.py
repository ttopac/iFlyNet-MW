import numpy as np
import matplotlib.pyplot as plt

vel = input ("Enter the vel to plot: ")
aoa = input ("Enter the aoa to plot: ")

trainData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/train_{}ms_{}deg.npy'.format(vel,aoa))

fig = plt.figure()
ax1 = fig.add_subplot(3,1,1)
ax2 = fig.add_subplot(3,1,2)
ax3 = fig.add_subplot(3,1,3)
fig.tight_layout(pad=2.0)

for i in range(6):
  ax1.plot(trainData[i,:], linewidth=0.3, label="PZT {}".format(i+1))
ax1.set_ylim(-1, 1)
leg1 = ax1.legend(fontsize=7, loc="upper right", ncol=2, columnspacing=1)
for line in leg1.get_lines():
  line.set_linewidth(1.5)
ax1.set_title("PZT data", fontsize=12)
ax1.set_xlabel("Time", fontsize=11)
ax1.set_ylabel("Signal (V)", labelpad=1, fontsize=11)
ax1.tick_params(labelsize="small")


for i in range(8):
  ax2.plot(trainData[i+6], linewidth=0.3, label="SG {}".format(i+1))
ax2.set_ylim(-0.1, 0.1)
leg2 = ax2.legend(fontsize=7, loc="upper right", ncol=3, columnspacing=1)
for line in leg2.get_lines():
  line.set_linewidth(1.5)
ax2.set_title("SG data", fontsize=12)
ax2.set_xlabel("Time", fontsize=11)
ax2.set_ylabel("Signal (V)", labelpad=1, fontsize=11)
ax2.tick_params(labelsize="small")


ax3.plot(trainData[14], linewidth=0.3, label="lift")
ax3.plot(trainData[15], linewidth=0.3, label="drag")
ax3.set_ylim(-100, 100)
leg3 = ax3.legend(fontsize=7, loc="upper right")
for line in leg3.get_lines():
  line.set_linewidth(1.5)
ax3.set_title("L/D", fontsize=12)
ax3.set_xlabel("Time", fontsize=11)
ax3.set_ylabel("Strain (s)", labelpad=1, fontsize=11)
ax3.tick_params(labelsize="small")


plt.show()