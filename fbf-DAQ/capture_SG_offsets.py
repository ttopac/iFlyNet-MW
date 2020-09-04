# This is a helper script to get SG offset coefficients for calibration.
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
from nidaqmx import stream_readers
from nidaqmx import Task
import numpy as np
from multiprocessing import Process, Pipe

# SGcoeffs = dict()
# SGcoeffs["amplifier_coeff"] = 100
# SGcoeffs["GF"] = 2.11
# SGcoeffs["Vex"] = 12

def calibrate_SGs(sample_rate, samples_to_read):
  with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai2") #SG_1
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai3") #SG_2
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0") #SG_3
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai1") #SG_4
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai2") #SG_5
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai3") #SG_6
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai0") #SG_7 (note SG_8 is missing)
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod4/ai2") #SG_9
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai0", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #Lift
    task.ai_channels.add_ai_strain_gage_chan("cDAQ1Mod8/ai2", strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I, voltage_excit_val=3.3, nominal_gage_resistance=351.4) #Drag
    task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=samples_to_read)

    calib_samples = np.zeros((10, samples_to_read))
    in_stream = nidaqmx._task_modules.in_stream.InStream(task)
    reader = stream_readers.AnalogMultiChannelReader(in_stream)
    reader.read_many_sample(calib_samples, number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE)
    
    # calib_samples[0:8] = -(4*calib_samples[0:8]/SGcoeffs["amplifier_coeff"]) / (2*calib_samples[0:8]/SGcoeffs["amplifier_coeff"]*SGcoeffs["GF"] + SGcoeffs["Vex"]*SGcoeffs["GF"])
    sgmean = np.mean(calib_samples, axis=1)
    print (sgmean)
    return sgmean

def send_SG_offsets(sample_rate, samples_to_read, child_conn):
  sgmean = calibrate_SGs(sample_rate, samples_to_read)
  child_conn.send(sgmean)
  child_conn.close()