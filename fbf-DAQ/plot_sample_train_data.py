import numpy as np
import matplotlib.pyplot as plt

# aveStrain = list()

# vel = input ("Enter the vel to plot: ")
# aoa = input ("Enter the aoa to plot: ")
vel = [16]
aoa = [0,4,8,12,14,16,17,18,19,20,21]

for v in vel:
  for a in aoa:
    trainData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/train_{}ms_{}deg.npy'.format(v,a))
    # trainData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/pre3/train_{}ms_{}deg.npy'.format(v,a))
    # aveStrain.append(-1*np.mean(trainData[6]))
    
    fig = plt.figure()
    ax1 = fig.add_subplot(1,1,1)
    ax2 = fig.add_subplot(3,1,2)
    ax3 = fig.add_subplot(3,1,3)
    fig.tight_layout(pad=2.0)

    for i in range(6):
      ax1.plot(trainData[i,:], linewidth=0.3, label="PZT {}".format(i+1))
    ax1.set_ylim(-0.05, 0.05)
    leg1 = ax1.legend(fontsize=7, loc="upper right", ncol=2, columnspacing=1)
    for line in leg1.get_lines():
      line.set_linewidth(1.5)
    ax1.set_title("PZT data", fontsize=12)
    ax1.set_xlabel("Time", fontsize=11)
    ax1.set_ylabel("Signal (V)", labelpad=1, fontsize=11)
    ax1.tick_params(labelsize="small")


    for i in range(1):
      ax2.plot(trainData[i+6], linewidth=0.3, label="SG {}".format(i+1))
    ax2.set_ylim(-0.4, 0.05)
    leg2 = ax2.legend(fontsize=7, loc="upper right", ncol=3, columnspacing=1)
    for line in leg2.get_lines():
      line.set_linewidth(1.5)
    ax2.set_title("SG data", fontsize=12)
    ax2.set_xlabel("Time", fontsize=11)
    ax2.set_ylabel("Signal (V)", labelpad=1, fontsize=11)
    ax2.tick_params(labelsize="small")


    ax3.plot(trainData[14], linewidth=0.3, label="lift")
    ax3.plot(trainData[15], linewidth=0.3, label="drag")
    ax3.set_ylim(-1000, 1000)
    leg3 = ax3.legend(fontsize=7, loc="upper right")
    for line in leg3.get_lines():
      line.set_linewidth(1.5)
    ax3.set_title("L/D", fontsize=12)
    ax3.set_xlabel("Time", fontsize=11)
    ax3.set_ylabel("Strain (s)", labelpad=1, fontsize=11)
    ax3.tick_params(labelsize="small")

    plt.show()
    # fig.savefig('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/plots/train_{}ms_{}deg.png'.format(v,a))


#Code for plotting average strain
# fig = plt.figure()
# ax1 = fig.add_subplot(1,1,1)
# ax1.set_title("Commercial SG Lift", fontsize=12)
# ax1.set_xlabel("Angle (deg)", fontsize=11)
# ax1.set_ylabel("Strain (%)", fontsize=11)
# ax1.plot(aoa, aveStrain, marker='o')
# plt.show()