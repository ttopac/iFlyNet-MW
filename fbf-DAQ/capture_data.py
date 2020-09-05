#This is a helper script to capture data from NI devices.
#Note that this is slow. There's a big overhead in with nidaqmx.Task(), and it's not feasible to start it every time. 
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
from nidaqmx import stream_readers
from nidaqmx import Task
import numpy as np
from multiprocessing import Process, Queue, Pipe
import time
import threading

# SGcoeffs = dict()
# SGcoeffs["amplifier_coeff"] = 100
# SGcoeffs["GF"] = 2.11
# SGcoeffs["Vex"] = 12

def capture_data_fixedlen(SGoffsets, sample_rate, samples_to_read):
  with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0") #0: PZT_1
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai1") #1: PZT_2
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai2") #2: PZT_3
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai3") #3: PZT_4
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai0") #4: PZT_5
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai1") #5: PZT_6
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai2") #6: SG_1
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai3") #7: SG_2
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0") #8: SG_3
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai1") #9: SG_4
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai2") #10: SG_5
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai3") #11: SG_6
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai0") #12: SG_7
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai2") #13: SG_9
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #14: Lift
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai2", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #15: Drag
    task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=samples_to_read)
    
    read_data = np.zeros((16, samples_to_read))
    in_stream = nidaqmx._task_modules.in_stream.InStream(task)
    reader = stream_readers.AnalogMultiChannelReader(in_stream)

    reader.read_many_sample(read_data, number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE, timeout=nidaqmx.constants.WAIT_INFINITELY)
    # read_data[6:14] = -(4*read_data[6:14]/SGcoeffs["amplifier_coeff"]) / (2*read_data[6:14]/SGcoeffs["amplifier_coeff"]*SGcoeffs["GF"] + SGcoeffs["Vex"]*SGcoeffs["GF"])
    read_data[6:,:] -= SGoffsets.reshape(SGoffsets.shape[0],-1) #Subtract the offset to obtain calibrated data
    read_data[14:,:] *= -1000000 #Convert to only commercial SGs to microstrains with correct sign, leave our SGs in volts.
    print ("DAQ sampling rate was: {}".format(task.timing.samp_clk_rate))
    return read_data

def capture_data_continuous(SGoffsets, sample_rate, samples_to_read):
  global read_data

  with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0") #0: PZT_1
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai1") #1: PZT_2
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai2") #2: PZT_3
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai3") #3: PZT_4
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai0") #4: PZT_5
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai1") #5: PZT_6
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai2") #6: SG_1
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai3") #7: SG_2
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0") #8: SG_3
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai1") #9: SG_4
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai2") #10: SG_5
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai3") #11: SG_6
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai0") #12: SG_7
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai2") #13: SG_9
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #14: Lift
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai2", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #15: Drag
    task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=samples_to_read*5)

    read_data = np.zeros((16, samples_to_read))
    in_stream = nidaqmx._task_modules.in_stream.InStream(task)
    reader = stream_readers.AnalogMultiChannelReader(in_stream)
    print ("DAQ sampling rate will be: {}".format(task.timing.samp_clk_rate))

    while True:
      reader.read_many_sample(read_data, number_of_samples_per_channel=samples_to_read, timeout=nidaqmx.constants.WAIT_INFINITELY)
      # read_data[6:14] = -(4*read_data[6:14]/SGcoeffs["amplifier_coeff"]) / (2*read_data[6:14]/SGcoeffs["amplifier_coeff"]*SGcoeffs["GF"] + SGcoeffs["Vex"]*SGcoeffs["GF"])
      read_data[6:,:] -= SGoffsets.reshape(SGoffsets.shape[0],-1) #Subtract the offset to obtain calibrated data
      read_data[14:,:] *= -1000000 #Convert to only commercial SGs to microstrains with correct sign, leave our SGs in volts.


def send_data(SGoffsets, sample_rate, samples_to_read, captype, child_conn=None):
  if captype == "fixedlen":
    read_data = capture_data_fixedlen(SGoffsets, sample_rate, samples_to_read)
    child_conn.send(read_data)
    child_conn.close()
  if captype == "continuous":
    capture_data_continuous(SGoffsets, sample_rate, samples_to_read)
