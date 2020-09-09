import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

read_data = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/noisetest_2.npy')

fig = plt.figure(figsize=(12.0, 6.0))
plt.style.use ('fivethirtyeight')
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
mpl.rcParams['axes.edgecolor'] = 'black'
mpl.rcParams['axes.linewidth'] = 1

ax1 = fig.add_subplot(3,1,1)
ax2 = fig.add_subplot(3,1,2)
ax3 = fig.add_subplot(3,1,3)

for i in range(6):
  ax1.plot (read_data[i], linewidth=0.5, label="PZT {}".format(i+1))
ax1.legend(fontsize=7, loc="upper right", ncol=1, columnspacing=1)
ax1.tick_params(labelsize="small")

for i in range(4,5):
  if i == 7:
    ax2.plot (read_data[6+i], linewidth=0.5, label="SG {}".format(i+2))
  else:
    ax2.plot (read_data[6+i], linewidth=0.5, label="SG {}".format(i+1))
ax2.legend(fontsize=7, loc="upper right", ncol=1, columnspacing=1)
ax2.tick_params(labelsize="small")

ax3.plot (read_data[14], linewidth = 1, label="Lift SG")
ax3.plot (read_data[15], linewidth = 1, label="Drag SG")
ax3.legend(fontsize=7, loc="upper right", ncol=1, columnspacing=1)
ax3.tick_params(labelsize="small")

plt.show()