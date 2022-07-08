#This is a helper script to capture data from NI devices.
#Note that this is slow. There's a big overhead in with nidaqmx.Task(), and it's not feasible to start it every time. 
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
from nidaqmx import stream_readers
import numpy as np
import time
import sys, os
from multiprocessing import Process, Queue, Pipe

def capture_data_fixedlen(sample_rate, samples_to_read, saveflag_conn):
  with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0") #0: PZT_1
    task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=samples_to_read)
    
    read_data = np.zeros((1, samples_to_read))
    in_stream = nidaqmx._task_modules.in_stream.InStream(task)
    reader = stream_readers.AnalogMultiChannelReader(in_stream)
    saveflag = True
    saveflag_conn.put_nowait(saveflag)

    while True:
      if saveflag_conn.qsize() >= 1:
        saveflag = saveflag_conn.get()
      if saveflag:
        print ("Started capturing data at {}".format(time.time()))
        reader.read_many_sample(read_data, number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE, timeout=nidaqmx.constants.WAIT_INFINITELY)
        print ("Completed DAQ at {}".format(time.time()))
        print ("DAQ sampling rate was: {}".format(task.timing.samp_clk_rate))
        break
      else:
        pass
    return read_data


if __name__ == "__main__":
  test_len = 0.25 #minutes. >1 is assumed to be drift test data, else training data.
  params = dict()
  params["sample_rate"] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 
  params["samples_read_main"] = int (params["sample_rate"]*60*test_len) 
  

  saveflag_conn = Queue()
  read_data = capture_data_fixedlen(params["sample_rate"], params["samples_read_main"], saveflag_conn)
  print (read_data[0:10])