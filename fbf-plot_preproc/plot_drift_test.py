import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

#Plotting stuff. Seems OK to ignore.
# def make_patch_spines_invisible(ax):
#   ax.set_frame_on(True)
#   ax.patch.set_visible(False)
#   for sp in ax.spines.values():
#     sp.set_visible(False)
# make_patch_spines_invisible(ax1_temptwin)
# ax1_temptwin.spines["right"].set_visible(True)

vel = '0'
aoa = '0'
test_folder = 'drift4_Sept8'
downsample_mult = 1700 #1700 is close to 1 datapoint per second since sampling rate is 1724.1379310344828 for drift test
plot_anemo_temp = True

# driftData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttest_{}ms_{}deg.npy'.format(test_folder,vel,aoa))
driftData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttest_{}ms_{}deg.npy'.format(test_folder,vel,aoa))
downsampled_SSNSGs = np.mean (-driftData[6:14,:].reshape(8,-1,downsample_mult), axis=2) #Downsample the sensor network SG data
downsampled_commSG = np.mean (driftData[14:,:].reshape(2,-1,downsample_mult), axis=2) #Downsample the Commercial SG data
xs = np.linspace(0,downsampled_commSG.shape[1]/60,downsampled_commSG.shape[1]) #Here /60 converts everything to minutes
if plot_anemo_temp:
  # tempdata = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttesttemp_{}ms_{}deg.npy'.format(test_folder,vel,aoa)
  tempdata = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttesttemp_{}ms_{}deg.txt'.format(test_folder,vel,aoa)
  df = pd.read_csv(tempdata, header=0, delim_whitespace=True)
  vel_np = df['Speed'].to_numpy()
  temp_np_F = df['Temp.'].to_numpy()
  temp_np_C = (temp_np_F-32) * 5 / 9

fig = plt.figure(figsize=(12.0, 6.0))
plt.style.use ('fivethirtyeight')
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
mpl.rcParams['axes.edgecolor'] = 'black'
mpl.rcParams['axes.linewidth'] = 1
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)

for i in range(8):
  if i == 7:
    ax1.plot (xs, downsampled_SSNSGs[i], linewidth=0.5, label="SG {}".format(i+2))
  else:
    ax1.plot (xs, downsampled_SSNSGs[i], linewidth=0.5, label="SG {}".format(i+1))
ax2.plot(xs, downsampled_commSG[0], linewidth=0.5, label="SG Lift")
ax2.plot(xs, downsampled_commSG[1], linewidth=0.5, label="SG Drag")

ax1.set_title("-SSN SG readings for V = {}m/s, AoA = {}deg".format(vel,aoa), fontsize=12)
ax1.set_xlabel("Time (min)", fontsize=11)
ax1.set_ylabel("Voltage (V)", fontsize=11)
ax1.legend(fontsize=7, loc="upper right", ncol=3, columnspacing=1)
ax1.tick_params(labelsize="small")
ax1.grid(False)

ax2.set_title("Commercial SG readings for V = {}m/s, AoA = {}deg".format(vel,aoa), fontsize=12)
ax2.set_xlabel("Time (min)", fontsize=11)
ax2.set_ylabel("Microstrain (us)", fontsize=11)
ax2.legend(fontsize=7, loc="upper right", ncol=1, columnspacing=1)
ax2.tick_params(labelsize="small")
ax2.grid(False)

if plot_anemo_temp:
  ax1_veltwin = ax1.twinx()
  ax1_temptwin = ax1.twinx()
  ax1_temptwin.spines["right"].set_position(("axes", 1.08))
  ax1_veltwin.plot (xs, vel_np[0:downsampled_commSG.shape[1]], "b-", linewidth=0.8,  label="WT Speed")
  ax1_temptwin.plot (xs, temp_np_C[0:downsampled_commSG.shape[1]], "r-", linewidth=0.8,  label="WT Temp")
  ax1_veltwin.set_ylabel("Airspeed (m/s)", fontsize=11)
  ax1_temptwin.set_ylabel("Temperature (C)", fontsize=11)
  ax1_veltwin.yaxis.label.set_color('b')
  ax1_temptwin.yaxis.label.set_color('r')
  ax1_veltwin.tick_params(colors = 'b', labelsize="x-small")
  ax1_temptwin.tick_params(colors = 'r', labelsize="x-small")
  ax1_temptwin.set_ylim((22,26))
  ax1_temptwin.grid(False)
  ax1_veltwin.grid(False)

  ax2_veltwin = ax2.twinx()
  ax2_temptwin = ax2.twinx()
  ax2_temptwin.spines["right"].set_position(("axes", 1.08))
  ax2_veltwin.plot (xs, vel_np[0:downsampled_commSG.shape[1]], "b-", linewidth=0.8,  label="WT Speed")
  ax2_temptwin.plot (xs, temp_np_C[0:downsampled_commSG.shape[1]], "r-", linewidth=0.8,  label="WT Temp")
  ax2_veltwin.set_ylabel("Airspeed (m/s)", fontsize=11)
  ax2_temptwin.set_ylabel("Temperature (C)", fontsize=11)
  ax2_veltwin.yaxis.label.set_color('b')
  ax2_temptwin.yaxis.label.set_color('r')
  ax2_veltwin.tick_params(colors = 'b', labelsize="x-small")
  ax2_temptwin.tick_params(colors = 'r', labelsize="x-small")
  ax2_temptwin.set_ylim((22,26))
  ax2_temptwin.grid(False)
  ax2_veltwin.grid(False)

plt.tight_layout(pad=2.0)
plt.show()