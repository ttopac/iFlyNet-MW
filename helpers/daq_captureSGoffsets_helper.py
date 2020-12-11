# This is a helper script to get SG nulling offset values for calibration.
# The calibration method for SSN SGs may not be true currently
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
from nidaqmx import stream_readers
from nidaqmx import Task
import numpy as np
from multiprocessing import Process, Pipe
import time

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
    task.ai_channels.add_ai_bridge_chan("cDAQ1Mod8/ai1", bridge_config=nidaqmx.constants.BridgeConfiguration.QUARTER_BRIDGE, voltage_excit_val=3.3, nominal_bridge_resistance=351.2) #LiftSG read as ai bridge
    task.ai_channels.add_ai_bridge_chan("cDAQ1Mod8/ai2", bridge_config=nidaqmx.constants.BridgeConfiguration.QUARTER_BRIDGE, voltage_excit_val=3.3, nominal_bridge_resistance=351.2) #DragSG read as ai bridge
    task.ai_channels.add_ai_rtd_chan("cDAQ1Mod7/ai0", rtd_type=nidaqmx.constants.RTDType.PT_3851, resistance_config=nidaqmx.constants.ResistanceConfiguration.FOUR_WIRE, current_excit_source=nidaqmx.constants.ExcitationSource.INTERNAL, current_excit_val=0.001, r_0=100) #RTD on rod
    task.ai_channels.add_ai_rtd_chan("cDAQ1Mod7/ai1", rtd_type=nidaqmx.constants.RTDType.PT_3851, resistance_config=nidaqmx.constants.ResistanceConfiguration.FOUR_WIRE, current_excit_source=nidaqmx.constants.ExcitationSource.INTERNAL, current_excit_val=0.001, r_0=100) #RTD on wing
    task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=samples_to_read)

    calib_samples = np.zeros((12, samples_to_read))
    in_stream = nidaqmx._task_modules.in_stream.InStream(task)
    reader = stream_readers.AnalogMultiChannelReader(in_stream)
    reader.read_many_sample(calib_samples, number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE, timeout=nidaqmx.constants.WAIT_INFINITELY)

    sgmean = np.mean(calib_samples, axis=1)
    sgmean[8:10] *= 3.3 #Multiply the ai values with excitation voltage to obtain initial voltage values.
    print ("SG initial voltages are (V): ", end="")
    print (sgmean)
    print ("Initial temperature at rod is: {}".format(sgmean[10]))
    print ("Initial temperature at wing is: {}".format(sgmean[11]))
    print ("SG calibration sampling rate was: {}".format(task.timing.samp_clk_rate))
    return sgmean[0:12]

def send_SG_offsets(sample_rate, samples_to_read, queue):
  sgmean = calibrate_SGs(sample_rate, samples_to_read)
  queue.put(sgmean)
