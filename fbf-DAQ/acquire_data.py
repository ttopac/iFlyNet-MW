import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
import matplotlib.pyplot as plt
import time
import numpy as np

def calibrate_SGs(params):
  with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai2") #SG_1
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai3") #SG_2
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0") #SG_3
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai1") #SG_4
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai2") #SG_5
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai3") #SG_6
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai0") #SG_7
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai2") #SG_9
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #Lift
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai1", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #Drag
    task.timing.cfg_samp_clk_timing(rate=params["sample_rate"], sample_mode=AcquisitionType.FINITE, samps_per_chan=params["sample_rate"])

    calib_samples = np.zeros((10, params["sample_rate"]))
    num_samples = task.read_many_sample(calib_samples, number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE)
    sgmean = np.mean(calib_samples, axis=1)
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
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai2") #PZT_3
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai3") #PZT_4
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai0") #PZT_5
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai1") #PZT_6
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai2") #SG_1
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai3") #SG_2
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0") #SG_3
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai1") #SG_4
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai2") #SG_5
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai3") #SG_6
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai0") #SG_7
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai2") #SG_9
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #Lift
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai1", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #Drag
    task.timing.cfg_samp_clk_timing(rate=params["sample_rate"], sample_mode=AcquisitionType.FINITE, samps_per_chan=params["samples_read_train"])
    
    train_samples = np.zeros((16, params["samples_read_train"]))
    num_samples = task.read_many_sample(train_samples, number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE)
    np.save('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/train_{}ms_{}deg.npy'.format(vel,aoa),train_samples)
    return aoa, vel


if __name__ == "__main__":
  params = dict()
  params["sample_rate"] = 7000
  params["samples_read_train"] = 100000
  aoa, vel = 99, 99

  sgmean = calibrate_SGs(params)
  while True:
    aoa, vel = get_data(aoa, vel, sgmean, params)