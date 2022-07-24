from operator import contains
from tkinter import Tk, Frame, Button, Label, Canvas
from tkinter import N, S, W, E
import numpy as np
import time
import sys, os
import tensorflow.keras
import keras_resnet
from multiprocessing import Queue, Process
from threading import Thread

sys.path.append(os.path.abspath('./helpers'))
import gui_windows_helper
import procestimates_helper
import streamdata_helper

# main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# main_folder = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/Macintosh HD/Users/tanay/GoogleDrive/Team Drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
main_folder = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/'
test_folder = 'Offline_Tests/offline11_Dec16/'
models_folder = 'Kerasfiles_Dec2020/'

models = dict()
models['types'] = ['stall', 'liftdrag']
models['filenames'] = ['stall_9sensors_train991_val994', 'reg_7sensors_train0020_val0022']
models['activesensors'] = [(0, 1, 2, 3, 4, 5, 6, 14, 15), (0, 1, 2, 3, 4, 5, 6)] #For regression, last 2 sensors give ground truth.
models['modelfiles'] = list()
models['means'] = np.array([-4.334589129779109e-06, 8.410618468135621e-05, 0.0003380918816729708, -0.00033040819902024725, -0.0004918243008301694, -0.00011952919733986609, -88.5091598596475, 0, 0, 0, 0, 0, 0, 0, -149.31235739451475, -1.4116125522601457, 0, 0])
models['stddevs'] = np.array([0.0011386681293641748, 0.0016901989191845132, 0.0012115932943635751, 0.0015570071919707178, 0.0012676181753638542, 0.0012784967994997837, 50.90707044913575, 0, 0, 0, 0, 0, 0, 0, 137.46263891169286, 39.068130385665526, 0, 0])
params = dict()
params ['sample_rate'] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 

def start_offline_button(GUIapp, streamhold_queue):
  startoffline_button = Button(GUIapp.parent, text='Click to start the stream...', command=lambda : streamhold_queue.put(False))
  startoffline_button.grid(row=0, column=2, rowspan=1, columnspan=2, sticky=S)


if __name__ == '__main__':
  #Define parameters
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.1 #seconds. This should be equal to or slower than 30hz (equal to or more than 0.033)
  keras_samplesize=233 #This is also used for pred_freq. Bad naming here.
  downsample_mult = keras_samplesize #For this app these two are  equal to have equal number of lift/drag values. 
  use_compensated_strains = True

  #Load the data and models
  leakyrelu = tensorflow.keras.layers.LeakyReLU(alpha=0.02)
  test_data = np.load(main_folder+test_folder+'/test.npy') #(18, ~2000000) channels: PZT1, PZT2, PZT3, PZT4, PZT5, PZT6, SG1, SG2, SG3, SG4, SG5, SG6, SG7, SG9, Lift, Drag, SG1RTD, WingRTD
  stepcount = int (test_data.shape[1] / params ['sample_rate'] / plot_refresh_rate) + 1
  models['filepaths'] = list(map(lambda x: main_folder+models_folder+'{}'.format(x), models['filenames']))
  for filepath in models['filepaths']:
    if os.path.isfile(filepath+'.hdf5'): #Old format saved with weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.hdf5', custom_objects={'LeakyReLU': leakyrelu}))
    elif os.path.isfile(filepath+'.tf'): #New format saved without weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.tf', custom_objects={'LeakyReLU': leakyrelu}))
      models['modelfiles'][-1].load_weights(filepath+'.ckpt')
    else:
      raise Exception ('Problem with loading Keras models') 

  #Run estimations on the data
  estimates = procestimates_helper.ProcEstimatesOffline(test_data, params['sample_rate'], plot_refresh_rate, downsample_mult, use_compensated_strains, models, keras_samplesize)
  estimates.make_estimates()
  
  #Initiate the streams of camera + measurements + estimations and place them on the GUI
  root = Tk()
  root.title ("Offline Ground Truth and i-FlyNet Estimation")
  title_labels = ("Measurements", "i-FlyNet Estimates")
  video_labels = ("AoA view", "Wing\nouter view")
  filespath = main_folder+test_folder
  camnums = ('2_deframed','1_deframed')
  
  GUIapp = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(root, plot_refresh_rate, downsample_mult, offline=True)
  GUIapp.init_UI(title_labels)
  GUIapp.draw_stall_lbl()
  GUIapp.draw_liftdrag_lbl()  
  GUIapp.initialize_queues_or_lists()

  data_cut = int (params['sample_rate'] * plot_refresh_rate)
  for i in range(stepcount): #(6001 for 300second of data with 20hz refresh rate)
    GUIapp.data_list.append(test_data[:, i*data_cut : (i+1)*data_cut])  
    GUIapp.stallest_list.append(estimates.stall_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.liftdragest_list.append(estimates.liftdrag_estimates[int(estimates.pred_count/stepcount*i)].reshape((1,-1)))
    GUIapp.shape_list.append(estimates.mfc_estimates[i])

  streamhold_queue = Queue()
  stream = streamdata_helper.StreamOffline(GUIapp, params, streamhold_queue, filespath, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate)
  stream.initialize_video(video_labels, camnums)
  stream.initialize_measurements()
  stream.initialize_estimates(True, True, True)
  GUIapp.place_on_grid(False, True, True)


  #Run the GUI
  start_offline_button(GUIapp, streamhold_queue)
  root.mainloop()