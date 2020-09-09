from multiprocessing import Process, Queue, Pipe
from threading import Thread
from capture_SG_offsets import send_SG_offsets
from capture_data import send_data
import numpy as np
import time

params = dict()
params["sample_rate"] = 1724.1379310344828 #Lowest sample rate possible is 1613 for our NI device. 1700 actually becomes 1724.1379310344828
params["samples_read_offset"] = int(1724.1379310344828) #Corresponds to ~1 sec of data.
params["samples_read_drift"] = int (5*6120000) #6120000 corresponds to 60 MINUTES of data.


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
    p = Process(target = send_data, args=(SGoffsets, params["sample_rate"], params["samples_read_drift"], "fixedlen", child_conn))
    p.start()
    read_data = parent_conn.recv()
    p.join()
    np.save('g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Training_Tests/drifttest_{}ms_{}deg.npy'.format(vel,aoa),read_data)