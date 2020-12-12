import sys
import os
import numpy as np
from tkinter import *
from tkinter import Tk, Frame, Button, Label, Canvas
from threading import Thread
import keras
import keras_resnet

sys.path.append(os.path.abspath('./helpers'))
import gui_windows_helper
import streamdata_helper

main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# main_folder = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'

models = dict()
models['types'] = ['stall', 'liftdrag']
models['filenames'] = ['stall_train993_val_988', 'lift_PZTonly_train_loss0461']
models['sensorcuts'] = [0 if 'PZTonly' in models['filenames'][i] else -2 for i in range(len(models['filenames']))]
models['modelfiles'] = list()
models['means'] = [-2.0175109479796352e-05, 0.00010905074475577042, 0.000394543100057414, -0.00028464991647680427, -0.0005756637708546992, -6.731485416880471e-05, -95.96163203982827, -24.0868367686678]
models['stddevs'] = [0.0012517186084292822, 0.0018231860855292457, 0.0010487415470856675, 0.0027847121382814344, 0.0013364316889671896, 0.00208186772161978, 108.47167144875641, 19.360939493624215]

params = dict()
params["sample_rate"] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 

if __name__ == "__main__":
  #Define parameters  
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.1 #seconds
  keras_samplesize=233 #This is also used for pred_freq. Bad naming here.
  downsample_mult = keras_samplesize #For this app these two are equal to have equal number of lift/drag values. 
  use_compensated_strains = False

  #Load the data and models
  leakyrelu = keras.layers.LeakyReLU(alpha=0.05)
  resnet_bn_layer = keras_resnet.layers.BatchNormalization(freeze=True)
  models['filepaths'] = list(map(lambda x: main_folder+'Kerasfiles/'+'{}'.format(x), models['filenames']))
  for filepath in models['filepaths']:
    if os.path.isfile(filepath+'.hdf5'): #Old format saved with weights (likely our shallow CNN model)
      models['modelfiles'].append(keras.models.load_model(filepath+'.hdf5', custom_objects={'LeakyReLU': leakyrelu}))
    elif os.path.isfile(filepath+'.tf'): #New format saved without weights (likely ResNet model)
      models['modelfiles'].append(keras.models.load_model(filepath+'.tf', custom_objects={'BatchNormalization':resnet_bn_layer}))
      models['modelfiles'][-1].load_weights(filepath+'.ckpt')
    else:
      raise Exception ('Problem with loading Keras models') 

  root = Tk()
  root.title ("Real-time Ground Truth and i-FlyNet Estimation")
  title_labels = ("Measurements", "i-FlyNet Estimates")
  video_names = ("AoA view", "Outer MFC view")
  camnums = (1,0)

  GUIapp = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(root, plot_refresh_rate, downsample_mult, offline=False)
  GUIapp.getSGoffsets(params)
  GUIapp.init_UI(title_labels)
  GUIapp.initialize_queues_or_lists()
  GUIapp.draw_stall_lbl()
  GUIapp.draw_liftdrag_lbl()  
  GUIapp.draw_videos(video_names, camnums)

  GUIapp.captureData(params)
  
  stream = streamdata_helper.StreamRealTime(GUIapp, params, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate)
  stream.init_and_stream_measurements()
  stream.init_and_stream_estimates(models)
  queue_refresh_thread = Thread(target=stream.refresh_queues)
  queue_refresh_thread.start()

  GUIapp.place_on_grid(False, True, True)

  root.mainloop()