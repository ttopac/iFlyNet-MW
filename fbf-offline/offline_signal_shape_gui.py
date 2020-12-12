from operator import contains
from tkinter import Tk, Frame, Button, Label, Canvas
from tkinter import N, S, W, E
import numpy as np
import time
import sys, os
from multiprocessing import Queue, Process
from threading import Thread

sys.path.append(os.path.abspath('./helpers'))
import gui_windows_helper
import procoffline_helper
import streamdata_helper

# main_folder = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# main_folder = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/Macintosh HD/Users/tanay/GoogleDrive/Team Drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
main_folder = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/'
test_folder = 'offline5_Nov19'

params = dict()
params ['sample_rate'] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 
params ['SG_offsets'] = np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) #Change this based on initial zero velocity conditions
params ['ref_temps'] = np.asarray([20, 20]) #Change this based on initial zero velocity conditions for RTDSG1 and RTDWing, respectively.

def start_offline_button(GUIapp, streamhold_queue):
  startoffline_button = Button(GUIapp.parent, text='Click to start the stream...', command=lambda : streamhold_queue.put(False))
  startoffline_button.grid(row=0, column=2, rowspan=1, columnspan=2, sticky=N)


if __name__ == '__main__':
  #Define parameters
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.1 #seconds
  downsample_mult = 233
  use_compensated_strains = False #NOT IMPLEMENTED YET FOR TRUE

  #Load data
  test_data = np.load(main_folder+'Offline_Tests/{}/test.npy'.format(test_folder))
  stepcount = int (test_data.shape[1] / params ['sample_rate'] / plot_refresh_rate) + 1

  #Run estimations on the data
  estimates = procoffline_helper.ProcEstimatesOffline(test_data, params['sample_rate'], plot_refresh_rate, downsample_mult, use_compensated_strains)
  estimates.make_estimates()
  
  #Initiate the streams of camera + measurements + estimations and place them on the GUI
  root = Tk()
  root.title ("Offline Video, Signals, and Shapes")
  video_labels = ("AoA view", "Outer MFC view")
  filespath = main_folder+'Offline_Tests/{}/'.format(test_folder)
  camnums = (1,0)
  
  GUIapp = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(root, plot_refresh_rate, downsample_mult, offline=True)
  GUIapp.SGoffsets = params ['SG_offsets']
  GUIapp.reftemps = params ['ref_temps']
  GUIapp.initialize_queues_or_lists()

  data_cut = int (params['sample_rate'] * plot_refresh_rate)
  for i in range(stepcount): #(601 for 60second of data with 10hz refresh rate)
    GUIapp.data_list.append(test_data[:, i*data_cut : (i+1)*data_cut])  
    GUIapp.shape_list.append(estimates.mfc_estimates[i])

  streamhold_queue = Queue()
  stream = streamdata_helper.StreamOffline(GUIapp, params, streamhold_queue, filespath, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate)
  stream.initialize_video(video_labels, camnums)
  stream.initialize_sensordata(True)
  stream.initialize_estimates(False, False, True)
  stream.GUIapp.place_on_grid(True, False, True)


  #Run the GUI
  start_offline_button(GUIapp, streamhold_queue)
  root.mainloop()