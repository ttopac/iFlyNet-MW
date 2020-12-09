from operator import contains
from tkinter import Tk, Frame, Button, Label, Canvas
from tkinter import N, S, W, E
import numpy as np
import time
import sys, os
import keras
import keras_resnet
from multiprocessing import Queue, Process
from threading import Thread

sys.path.append(os.path.abspath('./helpers'))
import gui_windows_helper
import procoffline_helper
import streamdata_helper

main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# main_folder = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/Macintosh HD/Users/tanay/GoogleDrive/Team Drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/'
test_folder, ref_temp = 'offline5_Nov19', 20.6590 #Reftemp is unique for test_folder and captured at the beginning of experiments. Set to None if prefer using first datapoint.
models = dict()
models['types'] = ['stall', 'liftdrag']
models['filenames'] = ['stall_train993_val_988', 'lift_PZTonly_train_loss0461']
models['sensorcuts'] = [0 if 'PZTonly' in models['filenames'][i] else -2 for i in range(len(models['filenames']))]
models['modelfiles'] = list()
models['means'] = [-2.0175109479796352e-05, 0.00010905074475577042, 0.000394543100057414, -0.00028464991647680427, -0.0005756637708546992, -6.731485416880471e-05, -95.96163203982827, -24.0868367686678]
models['stddevs'] = [0.0012517186084292822, 0.0018231860855292457, 0.0010487415470856675, 0.0027847121382814344, 0.0013364316889671896, 0.00208186772161978, 108.47167144875641, 19.360939493624215]

params = dict()
params ['sample_rate'] = 7142 #Use 7000 for training, 1700 for drift. 1700 becomes 1724.1379310344828. 7000 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 
params ['SG_offsets'] = np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) #Change this based on initial zero velocity conditions


def start_offline_button(GUIapp, streamhold_queue):
  startoffline_button = Button(GUIapp.parent, text='Click to start the stream...', command=lambda : streamhold_queue.put(False))
  startoffline_button.grid(row=0, column=2, rowspan=1, columnspan=2, sticky=S)


if __name__ == '__main__':
  #Define parameters
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.1 #seconds
  keras_samplesize=233 #This is also used for pred_freq. Bad naming here.
  downsample_mult = keras_samplesize #For this app these two are equal to have equal number of lift/drag values. 
  use_compensated_strains = False #NOT IMPLEMENTED YET FOR TRUE

  #Load the data and models
  leakyrelu = keras.layers.LeakyReLU(alpha=0.05)
  resnet_bn_layer = keras_resnet.layers.BatchNormalization(freeze=True)
  test_data = np.load(main_folder+'Offline_Tests/{}/test.npy'.format(test_folder))
  stepcount = int (test_data.shape[1] / params ['sample_rate'] / plot_refresh_rate) + 1
  models['filepaths'] = list(map(lambda x: main_folder+'Kerasfiles/'+'{}'.format(x), models['filenames']))
  for filepath in models['filepaths']:
    if os.path.isfile(filepath+'.hdf5'): #Old format saved with weights (likely our shallow CNN model)
      models['modelfiles'].append(keras.models.load_model(filepath+'.hdf5', custom_objects={'LeakyReLU': leakyrelu}))
    elif os.path.isfile(filepath+'.tf'): #New format saved without weights (likely ResNet model)
      models['modelfiles'].append(keras.models.load_model(filepath+'.tf', custom_objects={'BatchNormalization':resnet_bn_layer}))
      models['modelfiles'][-1].load_weights(filepath+'.ckpt')
    else:
      raise Exception ('Problem with loading Keras models') 

  #Run estimations on the data
  estimates = procoffline_helper.ProcEstimatesOffline(test_data, params['sample_rate'], plot_refresh_rate, downsample_mult, use_compensated_strains, models, keras_samplesize)
  estimates.make_estimates()
  
  #Initiate the streams of camera + measurements + estimations and place them on the GUI
  root = Tk()
  root.title ("Offline Ground Truth and i-FlyNet Estimation")
  title_labels = ("Measurements", "i-FlyNet Estimates")
  video_labels = ("AoA view", "Outer MFC view")
  filespath = main_folder+'Offline_Tests/{}/'.format(test_folder)
  camnums = (1,0)
  
  GUIapp = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(root, plot_refresh_rate, downsample_mult, offline=True)
  GUIapp.SGoffsets = params ['SG_offsets']
  GUIapp.init_UI(title_labels)
  GUIapp.draw_stall_lbl()
  GUIapp.draw_liftdrag_lbl()  
  GUIapp.initialize_queues_or_lists()

  data_cut = int (params['sample_rate'] * plot_refresh_rate)
  for i in range(stepcount): #(601 for 60second of data with 10hz refresh rate)
    GUIapp.data_list.append(test_data[:, i*data_cut : (i+1)*data_cut])  
    GUIapp.stallest_list.append(estimates.stall_estimates[i])
    GUIapp.liftdragest_list.append(estimates.liftdrag_estimates[i].reshape((1,-1)))
    GUIapp.shape_list.append(estimates.mfc_estimates[i])

  streamhold_queue = Queue()
  stream = streamdata_helper.StreamOffline(GUIapp, params, streamhold_queue, filespath, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate, ref_temp)
  stream.initialize_video(video_labels, camnums)
  stream.initialize_measurements()
  stream.initialize_estimates(True, True, True)
  GUIapp.place_on_grid(False, True, True)


  #Run the GUI
  start_offline_button(GUIapp, streamhold_queue)
  root.mainloop()