import sys
import time
import os
from multiprocessing import Queue
import pathlib

from tkinter import Tk, Button
from tkinter import S
import tensorflow.keras
import keras_resnet
import keras_resnet.models
import numpy as np
from threading import Thread

sys.path.append(os.path.abspath('./helpers'))
import streamdata_helper
import gui_windows_helper
import procestimates_helper

INCLUDE_STALL_EST = True
INCLUDE_LIFTDRAG_EST = True
INCLUDE_MFC_EST = True
INCLUDE_STATE_EST = True
INCLUDE_LIFTDRAG_TRUTH = False

file_path = pathlib.Path(__file__).parent.absolute()
# MAIN_LOC = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# MAIN_LOC = '/Volumes/Macintosh HD/Users/tanay/GoogleDrive/Team Drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# MAIN_LOC = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/'
MAIN_LOC = '/Volumes/GoogleDrive-109082130355562393140/Shared drives/WindTunnelTests-Feb2019/July2022_Tests_SNIC/'
# MAIN_LOC = 'g:/Shared drives/WindTunnelTests-Feb2019/July2022_Tests_SNIC/'

TEST_LOC = 'Offline_Tests/offline99_July20/'
MODELS_LOC = 'Kerasfiles_Dec2020/'
test_folder = os.path.join(MAIN_LOC, TEST_LOC)
models_folder = os.path.join(MAIN_LOC, MODELS_LOC)

models = dict()
models['types'] = ['stall', 'liftdrag', 'state']
# models['filenames'] = ['stall_9sensors_train991_val994', 'reg_7sensors_train0020_val0022', 'state_9sensors_train996_val972_July2022']
models['filenames'] = ['stall_9sensors_train991_val994', 'reg_7sensors_train0020_val0022', 'state_8sensors_July2022']
# models['activesensors'] = [(0, 1, 2, 3, 4, 5, 6, 14, 15), (0, 1, 2, 3, 4, 5, 6), (0, 1, 2, 3, 4, 5, 6, 14, 15)] #For regression, last 2 sensors give ground truth.
models['activesensors'] = [(0, 1, 2, 3, 4, 5, 6, 14, 15), (0, 1, 2, 3, 4, 5, 6), (0, 1, 2, 3, 4, 5, 14, 15)] #For regression, last 2 sensors give ground truth.
models['modelfiles'] = list()
models['means'] = np.array([-4.334589129779109e-06, 8.410618468135621e-05, 0.0003380918816729708, -0.00033040819902024725, -0.0004918243008301694, -0.00011952919733986609, -88.5091598596475, 0, 0, 0, 0, 0, 0, 0, -149.31235739451475, -1.4116125522601457, 0, 0])
models['stddevs'] = np.array([0.0011386681293641748, 0.0016901989191845132, 0.0012115932943635751, 0.0015570071919707178, 0.0012676181753638542, 0.0012784967994997837, 50.90707044913575, 0, 0, 0, 0, 0, 0, 0, 137.46263891169286, 39.068130385665526, 0, 0])
params = dict()
params ['sample_rate'] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 


if __name__ == '__main__':
  #Define parameters
  OFFLINE = True
  VISIBLE_DURATION = 15 #seconds. This is here to for compatibility with streamdata_helper
  DATA_REFRESH_RATE = 0.1 #seconds. This is the refresh rate of predictions
  KERAS_SAMPLESIZE = 233 #This is also used for pred_freq. Bad naming here.
  DOWNSAMPLE_MULT = KERAS_SAMPLESIZE #For this app these two are  equal to have equal number of lift/drag values.
  USE_COMPENSATED_STRAINS = False

  KERAS_EST = True
  MFC_EST = True
  LIFTDRAG_EST = True
  MFC_ESTIMATE_METH = 'simple' #simple or full
  LIFTDRAG_ESTIMATE_METH = 'sg1+vlm_v2' #choose amongst vlm, 1dcnn, sg1+vlm, sg1+vlm_v2, sg1+vlm_v2+xfoil

  ###
  #Load the data and models
  ###
  leakyrelu = tensorflow.keras.layers.LeakyReLU(alpha=0.02)
  resnet_model = keras_resnet.models.ResNet1D18(freeze_bn=True)
  resnet_bn_layer = keras_resnet.layers.ResNetBatchNormalization(freeze=True)
  test_data = np.load(os.path.join(test_folder,'test.npy')) #(18, ~2000000) channels: PZT1, PZT2, PZT3, PZT4, PZT5, PZT6, SG1, SG2, SG3, SG4, SG5, SG6, SG7, SG9, Lift, Drag, SG1RTD, WingRTD
  stepcount = int (test_data.shape[1] / params ['sample_rate'] / DATA_REFRESH_RATE) + 1
  models['filepaths'] = list(map(lambda x: models_folder+f'{x}', models['filenames']))
  for filepath in models['filepaths']:
    if os.path.isfile(filepath+'.hdf5'): #Old format saved with weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.hdf5', custom_objects={'LeakyReLU': leakyrelu, 'ResNet1D18':resnet_model, 'BatchNormalization':resnet_bn_layer}))
    elif os.path.isdir(filepath+'.tf'): #New format saved without weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.tf', custom_objects={'LeakyReLU': leakyrelu, 'ResNet1D18':resnet_model, 'BatchNormalization':resnet_bn_layer}))
    else:
      raise Exception ('Problem with loading Keras models')

  ###
  #Process i-FlyNet estimations. Either make new estimations and save or use cached ones.
  #All estimates are of size "stepcount".
  ###
  estimates = procestimates_helper.ProcEstimatesOffline(test_data, params['sample_rate'], DATA_REFRESH_RATE, DOWNSAMPLE_MULT, USE_COMPENSATED_STRAINS, models, KERAS_SAMPLESIZE)
  if USE_COMPENSATED_STRAINS:
    comp_SSNSG_data = estimates.sensor_data[6, :].reshape(1,-1)
    comp_commSG_data = estimates.sensor_data[14:16, :]
    test_data = np.concatenate((test_data, comp_SSNSG_data, comp_commSG_data), axis=0)

  estimates_path = os.path.join(test_folder, "saved_estimates"+"_"+MFC_ESTIMATE_METH+"_"+LIFTDRAG_ESTIMATE_METH)
  if not os.path.isdir(estimates_path): #Create a folder to put estimates if it doesn't already exists
    os.mkdir(estimates_path)
  if len(os.listdir(estimates_path)) < 4:  #All estimations are not there.
    estimates.make_estimates(KERAS_EST, MFC_EST, LIFTDRAG_EST, MFC_ESTIMATE_METH, LIFTDRAG_ESTIMATE_METH)
    #Save estimate files for easy reuse.
    if KERAS_EST:
      np.save(os.path.join(estimates_path,'stall_estimates.npy'), estimates.stall_estimates)
      np.save(os.path.join(estimates_path,'state_estimates.npy'), estimates.state_estimates)
    if MFC_EST:
      np.save(os.path.join(estimates_path,'mfc_estimates.npy'), estimates.mfc_estimates)
    if LIFTDRAG_EST:
      np.save(os.path.join(estimates_path,'liftdrag_estimates.npy'), estimates.liftdrag_estimates)
  else:
    #Load estimate files for reuse.
    if KERAS_EST:
      estimates.stall_estimates = np.load(os.path.join(estimates_path,'stall_estimates.npy'))
      estimates.state_estimates = np.load(os.path.join(estimates_path,'state_estimates.npy'))
    if MFC_EST:
      estimates.mfc_estimates = np.load(os.path.join(estimates_path,'mfc_estimates.npy'))
    if LIFTDRAG_EST:
      estimates.liftdrag_estimates = np.load(os.path.join(estimates_path,'liftdrag_estimates.npy'))
    
  ###
  # Initialize the data, estimations, history lists
  ###
  GUIapp = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(None, DATA_REFRESH_RATE, DOWNSAMPLE_MULT, OFFLINE, LIFTDRAG_ESTIMATE_METH)
  GUIapp.initialize_queues_or_lists()
  GUIapp.initialize_data_history(data_length=stepcount)

  ###
  # Get the data to the lists
  ###
  data_cut = int (params['sample_rate'] * DATA_REFRESH_RATE)
  for i in range(stepcount): #(3001 for 300second of data with 10hz refresh rate)
    relev_data = test_data[:, i*data_cut : (i+1)*data_cut]
    red_relev_data = np.mean(relev_data, axis=1)

    GUIapp.data_list.append(red_relev_data)
    GUIapp.stallest_list.append(estimates.stall_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.stateest_list.append(estimates.state_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.liftdragest_list.append(estimates.liftdrag_estimates[int(estimates.pred_count/stepcount*i)])
    GUIapp.shape_list.append(estimates.mfc_estimates[int(estimates.pred_count/stepcount*i)])

  GUIapp.update_data_history()
  
  ###
  # Save measured and predicted data
  ###
  np.save(os.path.join(test_folder, "sensor_dat.npy"),GUIapp.data_history["sensor_data"], allow_pickle=True) #PZTs(0-5) + 8SSNSGs(6-13) + 2commSGs(Lift&Drag)(14-15) + 2RTDs(16-17) + 3compensatedSGs(SG1,Lift,Drag)
  np.save(os.path.join(test_folder, "estimates_dat.npy"),GUIapp.data_history["estimates_data"], allow_pickle=True) #stall, airspeed, aoa, lift, drag, mfc1, mfc2
