import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
import matplotlib.pyplot as plt
import time
import numpy as np

def calibrate_SGs(params):
  with nidaqmx.Task() as task:
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #Lift
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai1", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #Drag
    task.timing.cfg_samp_clk_timing(rate=params["sample_rate"], sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=params["sample_rate"])
    sgsamples = np.asarray(task.read(number_of_samples_per_channel=params["samples_read"]))
    sgmean = np.mean(sgsamples)
    print(sgmean)
    return sgmean

def get_data(aoa, vel, sgmean, params):
  aoa_in = input ("Enter AoA of the test (deg): ")
  vel_in = input ("Enter freestream velocity of the test (m/s): ")

  aoa = aoa_in
  if vel_in != "":
    vel = vel_in

  t0 = time.time()
  with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0") #PZT_1
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai1") #PZT_2
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod6/ai2") #PZT_3
    
    task.timing.cfg_samp_clk_timing(rate=params["sample_rate"], sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=params["sample_rate"])
    testdata = np.zeros((4,1))
    
    while True:
      data = np.asarray(task.read(number_of_samples_per_channel=params["samples_read"]))
      data[3,:] -= sgmean
      data[3,:] *= 1000000
      testdata = np.concatenate((testdata,data),axis=1)
      t1 = time.time()
      if t1-t0 > 60:
        testdata = testdata[:,0:params["sample_rate"]*60]
        np.save('g:/Shared drives/WindTunnelTests-Feb2019/Nov2019_Tests/Baseline_Tests/sr=7000_str=2800_{}ms_{}deg.npy'.format(vel,aoa),testdata)
        return aoa, vel


if __name__ == "__main__":
  params = dict()
  params["samples_read"] = 2800
  params["sample_rate"] = 7000
  aoa, vel = 99, 99
  counter = 0

  sgmean = calibrate_SGs(params)
  while True:
    aoa, vel = get_data(aoa, vel, sgmean, params)