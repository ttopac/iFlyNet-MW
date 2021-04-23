from operator import contains
from tkinter import Tk, Frame, Button, Label, Canvas
from tkinter import N, S, W, E, NW
import numpy as np
import time
import sys, os
from pytesseract.pytesseract import main
import tensorflow.keras
import keras_resnet
import keras_resnet.models
from multiprocessing import Queue, Process
from threading import Thread
import cv2
import pathlib


sys.path.append(os.path.abspath('./helpers'))
import gui_windows_helper
import procoffline_helper
import streamdata_helper
import digitize_airspeed_helper
import digitize_aoa_helper

file_path = pathlib.Path(__file__).parent.absolute()

# main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# main_folder = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/Macintosh HD/Users/tanay/GoogleDrive/Team Drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
main_folder = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/'
test_folder = 'Offline_Tests/offline10_Dec16/'
models_folder = 'Kerasfiles_Dec2020/'

models = dict()
models['types'] = ['stall', 'liftdrag', 'state']
models['filenames'] = ['stall_9sensors_train991_val994', 'reg_7sensors_train0020_val0022', 'state_9sensors_train992_val972']
models['activesensors'] = [(0, 1, 2, 3, 4, 5, 6, 14, 15), (0, 1, 2, 3, 4, 5, 6), (0, 1, 2, 3, 4, 5, 6, 14, 15)] #For regression, last 2 sensors give ground truth.
models['modelfiles'] = list()
models['means'] = np.array([-4.334589129779109e-06, 8.410618468135621e-05, 0.0003380918816729708, -0.00033040819902024725, -0.0004918243008301694, -0.00011952919733986609, -88.5091598596475, 0, 0, 0, 0, 0, 0, 0, -149.31235739451475, -1.4116125522601457, 0, 0])
models['stddevs'] = np.array([0.0011386681293641748, 0.0016901989191845132, 0.0012115932943635751, 0.0015570071919707178, 0.0012676181753638542, 0.0012784967994997837, 50.90707044913575, 0, 0, 0, 0, 0, 0, 0, 137.46263891169286, 39.068130385665526, 0, 0])
params = dict()
params ['sample_rate'] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 

def start_offline_button(GUIapp, streamhold_queue):
  startoffline_button = Button(GUIapp.parent, text='Click to start the stream...', command=lambda : streamhold_queue.put(False))
  startoffline_button.grid(row=0, column=0, rowspan=1, columnspan=8, sticky=S)


if __name__ == '__main__':
  #Define parameters
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.1 #seconds. This should be equal to or slower than 30hz (equal to or more than 0.033)
  keras_samplesize=233 #This is also used for pred_freq. Bad naming here.
  downsample_mult = keras_samplesize #For this app these two are  equal to have equal number of lift/drag values. 
  use_compensated_strains = True
  mfc_estimate_meth = 'simple' #simple or full
  liftdrag_estimate_meth = 'sg1+vlm_v2' #vlm or 1dcnn or sg1+vlm or sg1+vlm_v2

  ###
  #Load the data and models
  ###
  leakyrelu = tensorflow.keras.layers.LeakyReLU(alpha=0.02)
  resnet_model = keras_resnet.models.ResNet1D18(freeze_bn=True)
  resnet_bn_layer = keras_resnet.layers.BatchNormalization(freeze=True)
  test_data = np.load(main_folder+test_folder+'/test.npy') #(18, ~2000000) channels: PZT1, PZT2, PZT3, PZT4, PZT5, PZT6, SG1, SG2, SG3, SG4, SG5, SG6, SG7, SG9, Lift, Drag, SG1RTD, WingRTD
  stepcount = int (test_data.shape[1] / params ['sample_rate'] / plot_refresh_rate) + 1
  models['filepaths'] = list(map(lambda x: main_folder+models_folder+'{}'.format(x), models['filenames']))
  for filepath in models['filepaths']:
    if os.path.isfile(filepath+'.hdf5'): #Old format saved with weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.hdf5', custom_objects={'LeakyReLU': leakyrelu, 'ResNet1D18':resnet_model, 'BatchNormalization':resnet_bn_layer}))
    elif os.path.isfile(filepath+'.tf'): #New format saved without weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.tf', custom_objects={'LeakyReLU': leakyrelu, 'ResNet1D18':resnet_model, 'BatchNormalization':resnet_bn_layer}))
      models['modelfiles'][-1].load_weights(filepath+'.ckpt')
    else:
      raise Exception ('Problem with loading Keras models') 

  ###
  #Process i-FlyNet estimations. Either make new estimations and save or use cached ones.
  #All estimates are of size "stepcount".
  ###
  estimates = procoffline_helper.ProcEstimatesOffline(test_data, params['sample_rate'], plot_refresh_rate, downsample_mult, use_compensated_strains, models, keras_samplesize)
  if len(os.listdir(main_folder+test_folder+"saved_estimates")) < 4: #All estimations are not there.
    #Make estimations
    estimates.make_estimates(True, True, True, mfc_estimate_meth, liftdrag_estimate_meth)
    #Save estimate files for easy reuse.
    np.save(main_folder+test_folder+"saved_estimates/"+'stall_estimates.npy', estimates.stall_estimates)
    np.save(main_folder+test_folder+"saved_estimates/"+'state_estimates.npy', estimates.state_estimates)
    np.save(main_folder+test_folder+"saved_estimates/"+'liftdrag_estimates.npy', estimates.liftdrag_estimates)
    np.save(main_folder+test_folder+"saved_estimates/"+'mfc_estimates.npy', estimates.mfc_estimates)
  else:
    #Load estimate files for reuse.
    estimates.stall_estimates = np.load(main_folder+test_folder+"saved_estimates/"+'stall_estimates.npy')
    estimates.state_estimates = np.load(main_folder+test_folder+"saved_estimates/"+'state_estimates.npy')
    estimates.liftdrag_estimates = np.load(main_folder+test_folder+"saved_estimates/"+'liftdrag_estimates.npy')
    estimates.mfc_estimates = np.load(main_folder+test_folder+"saved_estimates/"+'mfc_estimates.npy')
    

  ###
  #Process ground truth videos:
  ###
  if len(os.listdir(main_folder+test_folder+"saved_digitizations")) < 2: #All digitizations are not there.
    #Digitize the airspeed video
    airspeed_vid_path = main_folder+test_folder+"anemometer.mp4"
    ys_airspeed = digitize_airspeed_helper.digitize_airspeed(airspeed_vid_path)
    np.save(main_folder+test_folder+"saved_digitizations/"+'airspeed_digitized.npy', ys_airspeed, allow_pickle=True)
    #Store manually digitized aoa video as numpy array
    aoa_csv_path = main_folder+test_folder+"aoa_hist.csv"
    ys_aoa = digitize_aoa_helper.digitize_aoa(aoa_csv_path)
    np.save(main_folder+test_folder+"saved_digitizations/"+'aoa_digitized.npy', ys_aoa, allow_pickle=True)
  else: 
    ys_airspeed = np.load(main_folder+test_folder+"saved_digitizations/"+'airspeed_digitized.npy')
    ys_aoa = np.load(main_folder+test_folder+"saved_digitizations/"+'aoa_digitized.npy')


  ###
  #Initiate the streams of camera + measurements + estimations and place them on the GUI
  ###
  root = Tk()
  root.title ("Offline i-FlyNet")
  video_labels = ("Experiment Cam", "dummy")
  title_label = "Flight Characteristics"
  filespath = main_folder+test_folder
  camnums = ('1_deframed', '1_deframed')
  
  GUIapp = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(root, plot_refresh_rate, downsample_mult, offline=True, liftdrag_estimate_meth=liftdrag_estimate_meth)
  GUIapp.draw_midrow(title_label, os.path.join(file_path.parent, 'assets', 'legend.png'))
  GUIapp.draw_cartoon_cvs(os.path.join(file_path.parent, 'assets'))
  GUIapp.initialize_queues_or_lists()

  ###
  #Get data for GUI
  ###
  data_cut = int (params['sample_rate'] * plot_refresh_rate)
  for i in range(stepcount): #(3001 for 300second of data with 10hz refresh rate)
    relev_data = test_data[:, i*data_cut : (i+1)*data_cut]
    red_relev_data = np.mean(relev_data, axis=1)
    GUIapp.data_list.append(red_relev_data)  
    
    GUIapp.stallest_list.append(estimates.stall_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.stateest_list.append(estimates.state_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.liftdragest_list.append(estimates.liftdrag_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.shape_list.append(estimates.mfc_estimates[int(estimates.pred_count/stepcount*i)])

    try:
      GUIapp.meas_airspeed_list.append(ys_airspeed[round(i/(1/plot_refresh_rate))])
      GUIapp.meas_aoa_list.append(ys_aoa[round(i/(1/plot_refresh_rate))])
    except:
      GUIapp.meas_airspeed_list.append(ys_airspeed[-1])
      GUIapp.meas_aoa_list.append(ys_aoa[-1])
  
  ###
  #Finalize the GUI and start streaming.
  ###
  streamhold_queue = Queue()
  stream = streamdata_helper.StreamOffline(GUIapp, params, streamhold_queue, filespath, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate)
  stream.initialize_video(video_labels, camnums)
  stream.initialize_estimates(True, False, True, True, False, True)
  stream.initialize_plots_wcomparison(True, True, True, True)
  GUIapp.place_on_grid(False, False, False, True, True)


  #Run the GUI
  start_offline_button(GUIapp, streamhold_queue)
  root.mainloop()