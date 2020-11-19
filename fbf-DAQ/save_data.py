from multiprocessing import Process, Queue, Pipe
from threading import Thread
import numpy as np
import sys, os
sys.path.append(os.path.abspath('./helpers'))
from daq_captureSGoffsets_helper import send_SG_offsets
from daq_capturedata_helper import send_data

params = dict()
params["sample_rate"] = 1700 #Use 7000 for training, 1700 for drift. 1700 becomes 1724.1379310344828. 7000 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 
params["samples_read_offset"] = int(params["sample_rate"]) #Corresponds to ~1 sec of data.
params["samples_read_main"] = int (6120000*3) #Use 420000 for training (1 min), 6120000 for drift (60 mins).

if __name__ == "__main__":
  q1 = Queue()
  p1 = Thread(target = send_SG_offsets, args=(params["sample_rate"], params["samples_read_offset"], q1))
  p1.start()
  SGoffsets = q1.get()
  p1.join()
  
  aoa, vel = 99, 99
  while True:
    aoa_in = input ("Enter AoA of the test (deg): ")
    vel_in = input ("Enter freestream velocity of the test (m/s): ")
    aoa = aoa_in
    if vel_in != "":
      vel = vel_in

    parent_conn,child_conn = Pipe()
    saveflag_conn = Queue()
    p = Process(target = send_data, args=(SGoffsets, params["sample_rate"], params["samples_read_main"], "fixedlen", child_conn, saveflag_conn, 0, None))
    p.start()
    read_data = parent_conn.recv()
    p.join()
    np.save('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/drift11_Nov9/train_{}ms_{}deg.npy'.format(vel,aoa),read_data)