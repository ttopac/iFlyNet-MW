from multiprocessing import Process, Queue, Pipe
from capture_SG_offsets import send_SG_offsets
from capture_data import send_data
import numpy as np

params = dict()
params["sample_rate"] = 7000
params["samples_read_train"] = 420000 #Corresponds to 60 secs of data.


if __name__ == "__main__":
  parent_conn,child_conn = Pipe()
  p = Process(target = send_SG_offsets, args=(params["sample_rate"], params["sample_rate"], child_conn,))
  p.start()
  SGoffsets = parent_conn.recv()
  p.join()
  
  aoa, vel = 99, 99
  while True:
    aoa_in = input ("Enter AoA of the test (deg): ")
    vel_in = input ("Enter freestream velocity of the test (m/s): ")
    aoa = aoa_in
    if vel_in != "":
      vel = vel_in

    p = Process(target = send_data, args=(SGoffsets, params["sample_rate"], params["samples_read_train"], "fixedlen", child_conn)) #420000 for 60 seconds of data
    p.start()
    read_data = parent_conn.recv()
    p.join()
    np.save('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/train_{}ms_{}deg.npy'.format(vel,aoa),read_data)