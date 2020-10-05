#This is a helper script to capture data from NI devices.
#Note that this is slow. There's a big overhead in with nidaqmx.Task(), and it's not feasible to start it every time. 
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
from nidaqmx import stream_readers
import numpy as np

SGcoeffs = dict()
SGcoeffs["amplifier_coeff"] = 100
SGcoeffs["GF"] = 2.11
SGcoeffs["Vex"] = 12

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
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, initial_bridge_voltage=SGoffsets[8], nominal_gage_resistance=351.2) #Lift
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai2", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, initial_bridge_voltage=SGoffsets[9], nominal_gage_resistance=351.2) #Drag
    task.ai_channels.add_ai_rtd_chan("cDAQ1Mod7/ai0", rtd_type=nidaqmx.constants.RTDType.PT_3851, resistance_config=nidaqmx.constants.ResistanceConfiguration.FOUR_WIRE, current_excit_source=nidaqmx.constants.ExcitationSource.INTERNAL, current_excit_val=0.001, r_0=100)
    task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=samples_to_read)
    
    read_data = np.zeros((17, samples_to_read))
    in_stream = nidaqmx._task_modules.in_stream.InStream(task)
    reader = stream_readers.AnalogMultiChannelReader(in_stream)

    reader.read_many_sample(read_data, number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE, timeout=nidaqmx.constants.WAIT_INFINITELY)
    read_data[6:14,:] -= SGoffsets[0:8].reshape(SGoffsets[0:8].shape[0],-1) #Subtract the offset to obtain calibrated data
    read_data[6:14] = (4*read_data[6:14]/SGcoeffs["amplifier_coeff"]) / (2*read_data[6:14]/SGcoeffs["amplifier_coeff"]*SGcoeffs["GF"] + SGcoeffs["Vex"]*SGcoeffs["GF"])
    read_data[6:16,:] *= 1000000 #Convert all SGs to microstrains
    print ("DAQ sampling rate was: {}".format(task.timing.samp_clk_rate))
    return read_data

def capture_data_continuous(SGoffsets, sample_rate, samples_to_read, queue):
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
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, initial_bridge_voltage=SGoffsets[8], nominal_gage_resistance=351.2) #Lift SGoffsets[8]
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai2", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, initial_bridge_voltage=SGoffsets[9], nominal_gage_resistance=351.2) #Drag SGoffsets[9]
    task.ai_channels.add_ai_rtd_chan("cDAQ1Mod7/ai0", rtd_type=nidaqmx.constants.RTDType.PT_3851, resistance_config=nidaqmx.constants.ResistanceConfiguration.FOUR_WIRE, current_excit_source=nidaqmx.constants.ExcitationSource.INTERNAL, current_excit_val=0.001, r_0=100)
    task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=samples_to_read*100)

    read_data = np.zeros((17, samples_to_read))

    in_stream = nidaqmx._task_modules.in_stream.InStream(task)
    reader = stream_readers.AnalogMultiChannelReader(in_stream)
    print ("DAQ sampling rate will be: {}".format(task.timing.samp_clk_rate))
    print ("WARNING: CHANGE INIT BRIDGE VOLTAGE VALUES")

    while True:
      while queue.qsize() > 1: #This is here to keep up with delay in plotting.
        try:  
          a = queue.get_nowait()
        except:
          pass
      reader.read_many_sample(read_data, number_of_samples_per_channel=samples_to_read, timeout=nidaqmx.constants.WAIT_INFINITELY)
      read_data[6:14,:] -= SGoffsets[0:8].reshape(8,-1) #Subtract the offset from SSN SGs to obtain zeros. CommSGs are already zeroed above with initial voltage.
      read_data[6:14] = (4*read_data[6:14]/SGcoeffs["amplifier_coeff"]) / (2*read_data[6:14]/SGcoeffs["amplifier_coeff"]*SGcoeffs["GF"] + SGcoeffs["Vex"]*SGcoeffs["GF"])
      read_data[6:16,:] *= 1000000 #Convert all SGs to microstrains
      queue.put_nowait(read_data)


def send_data(SGoffsets, sample_rate, samples_to_read, captype, child_conn=None, save_duration=0):
  if captype == "fixedlen":
    read_data = capture_data_fixedlen(SGoffsets, sample_rate, samples_to_read)
    child_conn.send(read_data)
    child_conn.close()
  if captype == "continuous":
    capture_data_continuous(SGoffsets, sample_rate, samples_to_read, child_conn, save_duration)
