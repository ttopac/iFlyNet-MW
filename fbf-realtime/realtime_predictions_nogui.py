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
# import server_new_neuron

INCLUDE_STALL_EST = True
INCLUDE_LIFTDRAG_EST = True
INCLUDE_MFC_EST = True
INCLUDE_STATE_EST = True
INCLUDE_LIFTDRAG_TRUTH = False

file_path = pathlib.Path(__file__).parent.absolute()
# MAIN_LOC = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# MAIN_LOC = '/Volumes/Macintosh HD/Users/tanay/GoogleDrive/Team Drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# MAIN_LOC = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/'
# MAIN_LOC = '/Volumes/GoogleDrive-109082130355562393140/Shared drives/WindTunnelTests-Feb2019/July2022_Tests_SNIC/'
MAIN_LOC = 'g:/Shared drives/WindTunnelTests-Feb2019/July2022_Tests_SNIC/'

DATASAVE_LOC = 'Realtime_Tests/Test1/'
MODELS_LOC = 'Kerasfiles_Dec2020/'
datasave_folder = os.path.join(MAIN_LOC, DATASAVE_LOC)
models_folder = os.path.join(MAIN_LOC, MODELS_LOC)

models = dict()
models['types'] = ['stall', 'liftdrag', 'state']
models['filenames'] = ['stall_9sensors_train991_val994', 'reg_7sensors_train0020_val0022', 'state_9sensors_train996_val972_July2022']
models['activesensors'] = [(0, 1, 2, 3, 4, 5, 6, 14, 15), (0, 1, 2, 3, 4, 5, 6), (0, 1, 2, 3, 4, 5, 6, 14, 15)] #For regression, last 2 sensors give ground truth.
models['modelfiles'] = list()
models['means'] = np.array([-4.334589129779109e-06, 8.410618468135621e-05, 0.0003380918816729708, -0.00033040819902024725, -0.0004918243008301694, -0.00011952919733986609, -88.5091598596475, 0, 0, 0, 0, 0, 0, 0, -149.31235739451475, -1.4116125522601457, 0, 0])
models['stddevs'] = np.array([0.0011386681293641748, 0.0016901989191845132, 0.0012115932943635751, 0.0015570071919707178, 0.0012676181753638542, 0.0012784967994997837, 50.90707044913575, 0, 0, 0, 0, 0, 0, 0, 137.46263891169286, 39.068130385665526, 0, 0])
params = dict()
params ['sample_rate'] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 


if __name__ == '__main__':
  #Define parameters
  OFFLINE = False
  VISIBLE_DURATION = 15 #seconds. This is here to for compatibility with streamdata_helper
  DATA_REFRESH_RATE = 0.1 #seconds. This is the refresh rate of predictions
  KERAS_SAMPLESIZE = 233 #This is also used for pred_freq. Bad naming here.
  DOWNSAMPLE_MULT = KERAS_SAMPLESIZE #For this app these two are  equal to have equal number of lift/drag values.
  USE_COMPENSATED_STRAINS = False
  
  KERAS_EST = True
  MFC_EST = True
  LIFTDRAG_EST = True
  MFC_ESTIMATE_METH = 'simple' #simple or full
  LIFTDRAG_ESTIMATE_METH = 'sg1+vlm_v2' #choose amongst vlm, 1dcnn, sg1+vlm, sg1+vlm_v2

  ###
  #Load the data and models
  ###
  leakyrelu = tensorflow.keras.layers.LeakyReLU(alpha=0.02)
  resnet_model = keras_resnet.models.ResNet1D18(freeze_bn=True)
  resnet_bn_layer = keras_resnet.layers.ResNetBatchNormalization(freeze=True)
  models['filepaths'] = list(map(lambda x: models_folder+f'{x}', models['filenames']))
  for filepath in models['filepaths']:
    if os.path.isfile(filepath+'.hdf5'): #Old format saved with weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.hdf5', custom_objects={'LeakyReLU': leakyrelu, 'ResNet1D18':resnet_model, 'BatchNormalization':resnet_bn_layer}))
    elif os.path.isdir(filepath+'.tf'): #New format saved without weights
      models['modelfiles'].append(tensorflow.keras.models.load_model(filepath+'.tf', custom_objects={'LeakyReLU': leakyrelu, 'ResNet1D18':resnet_model, 'BatchNormalization':resnet_bn_layer}))
    else:
      raise Exception ('Problem with loading Keras models')

  ###
  # Get initial SG values and initialize the data, estimations, history lists
  ###
  GUIapp = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(None, DATA_REFRESH_RATE, DOWNSAMPLE_MULT, OFFLINE, LIFTDRAG_ESTIMATE_METH)
  GUIapp.getSGoffsets(params)
  GUIapp.initialize_queues_or_lists()
  GUIapp.initialize_data_history()
  GUIapp.start_datacapture_process(params)

  ###
  # Start streaming data
  ###
  stream = streamdata_helper.StreamRealTime(GUIapp, params, USE_COMPENSATED_STRAINS, DOWNSAMPLE_MULT, VISIBLE_DURATION, DATA_REFRESH_RATE, False)  
  # stream.init_sensordata()
  queue_refresh_thread = Thread(target=stream.refresh_queues)
  queue_refresh_thread.start()
  
  ###
  # Start making predictions
  ###
  estimates_queue = [GUIapp.stallest_queue, GUIapp.stateest_queue, GUIapp.liftdragest_queue, GUIapp.shape_queue]
  estimates = procestimates_helper.ProcEstimatesRealtime(GUIapp.data_queue, estimates_queue, params ['sample_rate'], DATA_REFRESH_RATE, DOWNSAMPLE_MULT, USE_COMPENSATED_STRAINS, KERAS_EST, MFC_EST, LIFTDRAG_EST, MFC_ESTIMATE_METH, LIFTDRAG_ESTIMATE_METH, models, KERAS_SAMPLESIZE)
  
  estimatesdata_prep_thread = Thread(target=estimates.prepare_data)
  stallestimate_thread = Thread(target=estimates.estimate_stall)
  stateestimate_thread = Thread(target=estimates.estimate_state)
  mfcestimate_thread = Thread(target=estimates.estimate_mfc)
  liftdragestimate_thread = Thread(target=estimates.estimate_liftdrag)
  
  estimatesdata_prep_thread.start()
  stallestimate_thread.start()
  stateestimate_thread.start()
  mfcestimate_thread.start()
  liftdragestimate_thread.start()
  
  ###
  # Atharva's streaming thread
  ###
  # raw_sensors = GUIapp.data_history["sensor_data"]
  # estimates = GUIapp.data_history["estimates_data"]
  # data_stream = server_new_neuron.ServerFunction()
  # mylist_increment_thread = Thread(target=data_stream.increase_num, args=[mylist])
  # data_stream.start()
  # mylist_increment_thread.start()

  ###
  # Update measured and predicted data
  ###
  stream.update_datahistory()

  start_time = time.time()
  while time.time() - start_time < 1200:
    raw_sensors = GUIapp.data_history["sensor_data"][:,-1] #PZTs(0-5) + 8SSNSGs(6-13) + 2commSGs(Lift&Drag)(14-15) + 2RTDs(16-17)
    estimates = GUIapp.data_history["estimates_data"][:,-1] #stall, airspeed, aoa, lift, drag, mfc1, mfc2
    print ("Raw sensor data:")
    print (f"commSG Lift: {raw_sensors[14]}, commSG Drag: {raw_sensors[15]}")
    print (f"SSNSG Lift: {raw_sensors[6]}")
    print ("Estimates:")
    print (f"Stall: {estimates[0]}, Airspeed: {estimates[1]}, AoA: {estimates[2]}, Lift: {estimates[3]}, Drag: {estimates[4]}, MFC1: {estimates[5]}, MFC2: {estimates[6]} \n")
    print ()
    time.sleep(1)
  np.save(os.path.join(datasave_folder, "sensor_dat.npy"),GUIapp.data_history["sensor_data"], allow_pickle=True)
  np.save(os.path.join(datasave_folder, "estimates_dat.npy"),GUIapp.data_history["estimates_data"], allow_pickle=True)
