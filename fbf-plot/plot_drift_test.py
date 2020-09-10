import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import sys, os
from scipy import signal
sys.path.append(os.path.abspath('./helpers'))
from plot_sensordata_helper import PlotSensorData

vel = '0_2'
aoa = '0_2'
test_folder = 'drift5_Sept9'
downsample_mult = 1700 #1700 is close to 1 datapoint per second since sampling rate is 1724.1379310344828 for drift test

plot_anemo_temp = True
plot_commSG_comp = True
poly_coeffs = (-23.65, 2.06, -5.02E-2, 2.26E-4, 0.3, 0.219)
gage_fact, k_poly = 2, 2
gage_fact_CTE, SG_matl_CTE = 93E-6, 10.8E-6
al6061_CTE = 23.6E-6

# driftData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttest_{}ms_{}deg.npy'.format(test_folder,vel,aoa))
driftData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttest_{}ms_{}deg.npy'.format(test_folder,vel,aoa))
downsampled_SSNSGs = np.mean (-driftData[6:14,:].reshape(8,-1,downsample_mult), axis=2) #Downsample the sensor network SG data
downsampled_commSGs = np.mean (driftData[14:,:].reshape(2,-1,downsample_mult), axis=2) #Downsample the Commercial SG data
downsampled_PZTs = signal.resample(driftData[0:6,:], downsampled_commSGs.shape[1], axis=1)
ys = np.concatenate ((downsampled_PZTs, downsampled_SSNSGs, downsampled_commSGs), axis=0)
visible_duration = ys.shape[1]/60 #Here /60 converts everything from seconds to minutes.

plot = PlotSensorData(visible_duration, downsample_mult)
plot.plot_raw_lines(realtime=False, ys=ys, vel=vel, aoa=aoa)

if plot_anemo_temp:
  # tempdata = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttesttemp_{}ms_{}deg.npy'.format(test_folder,vel,aoa)
  tempdata = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttesttemp_{}ms_{}deg.txt'.format(test_folder,vel,aoa)
  df = pd.read_csv(tempdata, header=0, delim_whitespace=True)
  vel_np = df['Speed'].to_numpy()[0:downsampled_commSGs.shape[1]]
  temp_np_F = df['Temp.'].to_numpy()[0:downsampled_commSGs.shape[1]]
  plot.plot_anemometer_data (vel_np, temp_np_F)

if plot_commSG_comp:
  plot.plot_commSG_tempcomp_lines(temp_np_F, poly_coeffs, gage_fact_CTE, SG_matl_CTE, al6061_CTE, gage_fact, k_poly)

plot.term_common_params(realtime=False)
plt.show()