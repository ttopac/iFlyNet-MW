from multiprocessing import Process, Queue, Pipe
from threading import Thread
import numpy as np
from scipy import signal
import sys, os
sys.path.append(os.path.abspath('./helpers'))
from daq_captureSGoffsets_helper import send_SG_offsets
from daq_capturedata_helper import send_data

continuous_collect = False
test_type = 'train' #drift or train
test_folder = 'Test_Tests/test4_Dec14'
test_len = 0.25 #minutes. >1 is assumed to be drift test data, else training data.

params = dict()
params["sample_rate"] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 
downsample_mult = 1 #Use 1 for training, use 233 for drifttest.
params["samples_read_offset"] = int(params["sample_rate"]) #Corresponds to ~1 sec of data.
params["samples_read_main"] = int (params["sample_rate"]*60*test_len) 
num_samples = int(params["samples_read_main"]/downsample_mult)

if __name__ == "__main__":
  q1 = Queue()
  p1 = Thread(target = send_SG_offsets, args=(params["sample_rate"], params["samples_read_offset"], q1))
  p1.start()
  SGoffsets = q1.get()
  p1.join()
  
  aoa, vel = 0, 0
  ref_test = True
  while True:
    if continuous_collect:
      aoa_in = aoa+1
      vel_in = vel+1
    else:
      aoa_in = input ("Enter AoA of the test (deg): ")
      vel_in = input ("Enter freestream velocity of the test (m/s): ")
    
    aoa = aoa_in
    if vel_in != "":
      vel = vel_in

    filename = '{}ms_{}deg_{}min.npy'.format(vel,aoa,test_len)
    if test_type == 'drift':
      filename = 'drift_' + filename
    elif test_type == 'train':
      filename = 'train_' + filename
    if ref_test == True:
      filename = 'REF_' + filename

    parent_conn,child_conn = Pipe()
    saveflag_conn = Queue()
    p = Process(target = send_data, args=(SGoffsets, params["sample_rate"], params["samples_read_main"], "fixedlen", child_conn, saveflag_conn, 0, None))
    p.start()
    read_data = parent_conn.recv()
    p.join()

    useful_data_start, useful_data_end = 0, int(read_data.shape[1]/downsample_mult)*downsample_mult
    fewerPZTdata = signal.resample(read_data[0:6,:], num_samples, axis=1) #Downsample the PZT data
    fewerotherdata = np.mean (read_data[6:,useful_data_start:useful_data_end].reshape(read_data.shape[0]-6,-1,downsample_mult), axis=2) #Downsample the SSNSG data
    downsampled_data = np.concatenate((fewerPZTdata, fewerotherdata), axis=0)
    ref_test = False

    # np.save('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/{}/{}'.format(test_folder,filename),downsampled_data)
    np.save('c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/{}/{}'.format(test_folder,filename),downsampled_data)