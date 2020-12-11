#This script is used for plotting long-term raw SG data along with compensated values (calculated in helper function) to test compensation performance.
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import sys, os
from scipy import signal
sys.path.append(os.path.abspath('./helpers'))
import plot_sensordata_helper

SGcoeffs = dict()
SGcoeffs["amplifier_coeff"] = 100
SGcoeffs["GF"] = 2.11
SGcoeffs["Vex"] = 12

SSNSG_voltage = False #(True if data is before Sept. 13) We collected SSNSG data as voltage in all experiments before Sept. 13. They need conversion to microstrain
commSGdata_reverted = False #(True if data is before Sept. 13) We multiplied CommSG data by -1 in all experiments before Sept. 13.
vel = '2'
aoa = '2'
test_len = '120' #minutes
test_folder = 'drift26_Dec10'
test_file = 'drift_{}ms_{}deg_{}min.npy'.format(vel,aoa,test_len)
ref_temp_file = test_file
downsample_mult = 1700 #Only used if data is not already downsampled. 1700 is close to 1 datapoint per second since sampling rate is 1724.1379310344828 for drift test

temp_source = 'RTD' #Options are None, 'anemometer', or 'RTD'. Anemometer is deprecated!!!
plot_temp_line = True
plot_commSG_comp = True
plot_SSNSG_comp = True
if temp_source == None:
  plot_temp_line, plot_commSG_comp, plot_SSNSG_comp = False, False, False


if __name__ == "__main__":
  # driftData = np.load('c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/Drift_Tests/{}/{}'.format(test_folder,test_file))
  # driftData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Drift_Tests/{}/{}'.format(test_folder,test_file))
  # driftData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Drift_Tests/{}/{}'.format(test_folder,test_file))
  # driftData = np.load('/Volumes/Macintosh HD/Users/tanay/GoogleDrive/Team Drives/WindTunnelTests-Feb2019/Sept2020_Tests/Drift_Tests/{}/{}'.format(test_folder,test_file))
  driftData = np.load('/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/Drift_Tests/{}/{}'.format(test_folder,test_file))
  if ref_temp_file != test_file:
    ref_temp_data = np.load('/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/Drift_Tests/{}/{}'.format(test_folder,ref_temp_file))
    ref_temp = ref_temp_data[16:18,0]
  else:
    ref_temp = driftData[16:18,0]

  
  if driftData.shape[1] > 500000: #Not downsampled at capture time
    raise NotImplementedError #Deprecated after Sept 2020 tests. See previous commits if needed.
  else: #Data downsampled at capture time
    ys = driftData
  xs = np.linspace(0,int(test_len),ys.shape[1]) 

  plot = plot_sensordata_helper.PlotSensorData(1, False, False, True, ref_temp)
  plot.plot_raw_lines(xs, ys=ys, vel=vel, aoa=aoa)

  if temp_source == 'RTD':
    temp_np_C_SG1 = ys[16]
    temp_np_C_wing = ys[17]

  if plot_temp_line:
    plot.plot_RTD_data (temp_np_C_SG1, temp_np_C_wing)

  if plot_commSG_comp:
    plot.plot_commSG_tempcomp_lines(temp_np_C_SG1, temp_np_C_wing)

  if plot_SSNSG_comp:
    plot.plot_SSNSG_tempcomp_lines(temp_np_C_SG1, temp_np_C_wing)

  plot.term_common_params(mfcplot_exists=False)
  plt.show()