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
commSGdata_reverted = False #(True if data is before Sept. 13) We multiplied CommSG data with -1 in all experiments before Sept. 13.
vel = '0_3'
aoa = '0_3'
test_folder = 'drift8_Sept15'
downsample_mult = 1700 #1700 is close to 1 datapoint per second since sampling rate is 1724.1379310344828 for drift test

temp_source = 'RTD' #Options are None, 'anemometer', or 'RTD'
plot_temp_line = True
plot_commSG_comp = True
plot_SSNSG_comp = True
if temp_source == None:
  plot_temp_line, plot_commSG_comp, plot_SSNSG_comp = False, False, False

#Comm. SG compensation parameters
poly_coeffs = (-23.65, 2.06, -5.02E-2, 2.26E-4, 0.3, 0.219)
gage_fact, k_poly = 2, 2
gage_fact_CTE, SG_matl_CTE = 93E-6, 10.8E-6
al6061_CTE = 23.6E-6

#SSN SG compensation parameters (skipping SG8)
r_total = np.asarray ([14, 14.4, 14.1, 15.3, 14.7, 14, 14.3, 13.9])
r_wire = np.asarray ([0.2, 0.2, 0.3, 1.1, 0.2, 0.2, 0.5, 0.1]) #Approx from drift8_Sept15_0_3 test.
# r_wire = np.asarray ([0.2, 0.6, 0.3, 1.5, 0.9, 0.2, 0.5, 0.1]) #From Xiyuan
alpha_gold = 1857.5
alpha_constantan = 21.758

if __name__ == "__main__":
  # driftData = np.load('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttest_{}ms_{}deg.npy'.format(test_folder,vel,aoa))
  driftData = np.load('/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttest_{}ms_{}deg.npy'.format(test_folder,vel,aoa))
  downsampled_SSNSGs = np.mean (driftData[6:14,:].reshape(8,-1,downsample_mult), axis=2) #Downsample the sensor network SG data
  if SSNSG_voltage: downsampled_SSNSGs = 1e6*(4*downsampled_SSNSGs/SGcoeffs["amplifier_coeff"]) / (2*downsampled_SSNSGs/SGcoeffs["amplifier_coeff"]*SGcoeffs["GF"] + SGcoeffs["Vex"]*SGcoeffs["GF"])
  downsampled_commSGs = np.mean (driftData[14:16,:].reshape(2,-1,downsample_mult), axis=2) #Downsample the Commercial SG data
  if commSGdata_reverted: downsampled_commSGs *= -1
  downsampled_PZTs = signal.resample(driftData[0:6,:], downsampled_commSGs.shape[1], axis=1)
  ys = np.concatenate ((downsampled_PZTs, downsampled_SSNSGs, downsampled_commSGs), axis=0)
  visible_duration = ys.shape[1]/60 #Here /60 converts everything from seconds to minutes.

  plot = plot_sensordata_helper.PlotSensorData(visible_duration, downsample_mult)
  plot.plot_raw_lines(realtime=False, ys=ys, vel=vel, aoa=aoa)

  if temp_source == 'anemometer':
    # tempdata = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttesttemp_{}ms_{}deg.txt'.format(test_folder,vel,aoa)
    tempdata = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/{}/drifttesttemp_{}ms_{}deg.txt'.format(test_folder,vel,aoa)
    df = pd.read_csv(tempdata, header=0, delim_whitespace=True)
    vel_np = df['Speed'].to_numpy()[0:downsampled_commSGs.shape[1]]
    temp_np_F = df['Temp.'].to_numpy()[0:downsampled_commSGs.shape[1]]
    temp_np_C = (temp_np_F-32) * 5 / 9
  elif temp_source == 'RTD':
    temp_np_C = driftData[16]
    temp_np_C = np.mean (temp_np_C.reshape(-1,downsample_mult), axis=1) #Downsample the sensor network SG data

  if plot_temp_line:
    if temp_source == 'anemometer':
      plot.plot_anemometer_data (vel_np, temp_np_C)
    else:
      plot.plot_RTD_data (temp_np_C)

  if plot_commSG_comp:
    plot.plot_commSG_tempcomp_lines(temp_np_C, poly_coeffs, gage_fact_CTE, SG_matl_CTE, al6061_CTE, gage_fact, k_poly)

  if plot_SSNSG_comp:
    plot.plot_SSNSG_tempcomp_lines(temp_np_C, r_total, r_wire, alpha_gold, alpha_constantan)

  plot.term_common_params(realtime=False)
  plt.show()