#%% Import libraries
import numpy as np
import matplotlib.pyplot as plt
import os
import pickle
import process_utils
from keras import models
from keras.models import load_model

os.environ['KMP_DUPLICATE_LIB_OK']='True'
with open ('/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/KerasFiles/06222019_training/stateDict.pickle', 'rb') as handle:
  stateDict = pickle.load(handle)

#%% Run 2deg and 20deg from March2019 and June2019 tests. Confirm both of them predict correct stall behavior
# For March2019 data
dataloc = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/Test Data/Raw Data/'
incSensors = ('PZTLB',)

dat_mar_2deg = process_utils.convert_to_np_labview_multi(txt_file=dataloc+'03.30 20m s ★/txt/Airspeed20_AOA2.txt', sensors=incSensors, windowsize=2800)
dat_mar_2deg = np.reshape(dat_mar_2deg,(-1,2800,len(incSensors)))
for i in range(30,40):
  stall_prob = process_utils.predict1d(data=dat_mar_2deg[i,:,:], model=myclassifier, windowsize=2800, sensorcount=len(incSensors))
  print ('Stall probability of March 2deg test point #{} = {}'.format(i*2800, stall_prob))

dat_mar_20deg = process_utils.convert_to_np_labview_multi(txt_file=dataloc+'03.30 20m s ★/txt/Airspeed20_AOA20.txt', sensors=incSensors, windowsize=2800)
dat_mar_20deg = np.reshape(dat_mar_20deg,(-1,2800,len(incSensors)))
for i in range(30,40):
  stall_prob = process_utils.predict1d(data=dat_mar_20deg[i,:,:], model=myclassifier, windowsize=2800, sensorcount=len(incSensors))
  print ('Stall probability of March 20deg test point #{} = {}'.format(i*2800, stall_prob))

#%% For June2019 data
dataloc = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/FreqTest/'
incSensors = ('PZTLB',)

dat_jun_2deg = np.load(dataloc+'714285714_20ms_2deg.npy')
maxdivisor = dat_jun_2deg.shape[1]//2800
dat_jun_2deg = np.reshape(dat_jun_2deg[0:len(incSensors),0:maxdivisor*2800],(-1,2800,len(incSensors)))
for i in range(0,10):
  stall_prob = process_utils.predict1d(data=dat_jun_2deg[i,:,:], model=myclassifier, windowsize=2800, sensorcount=len(incSensors))
  print ('Stall probability of June 2deg test point #{} = {}'.format(i*2800, stall_prob))

dat_jun_20deg = np.load(dataloc+'714285714_20ms_20deg.npy')
maxdivisor = dat_jun_20deg.shape[1]//2800
dat_jun_20deg = np.reshape(dat_jun_20deg[0:len(incSensors),0:maxdivisor*2800],(-1,2800,len(incSensors)))
for i in range(30,40):
  stall_prob = process_utils.predict1d(data=dat_jun_20deg[i,:,:], model=myclassifier, windowsize=2800, sensorcount=len(incSensors))
  print ('Stall probability of June 20deg test point #{} = {}'.format(i*2800, stall_prob))

#%% For June2019 data standardized
myclassifier = load_model('/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/KerasFiles/06222019_training/UnfilteredData/06222019_StallOnly_96val_2800_3pzt_std.h5')
dataloc = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/FreqTest/'
incSensors = ('PZTLB','PZTLT','PZTRB')
means = [-0.0002862905522754296, 0.00014160949504295255, 2.983585730877926e-05, -36.33824690045131] # As obtained by training data
stddevs = [0.023828177361846174, 0.012151506564682033, 0.021041555452279762, 15.658515723288968] # As obtained by training data


dat_jun_2deg = np.load(dataloc+'714285714_20ms_2deg.npy')
maxdivisor = dat_jun_2deg.shape[1]//2800
dat_jun_2deg = np.reshape(dat_jun_2deg[0:len(incSensors),0:maxdivisor*2800],(-1,2800,len(incSensors)))
for i in range(3):
  dat_jun_2deg[:,:,i] = (dat_jun_2deg[:,:,i]-means[i])/stddevs[i]
for i in range(0,10):
  stall_prob = process_utils.predict1d(data=dat_jun_2deg[i,:,:], model=myclassifier, windowsize=2800, sensorcount=len(incSensors))
  print ('Stall probability of June 2deg test point #{} = {}'.format(i*2800, stall_prob))

dat_jun_20deg = np.load(dataloc+'714285714_20ms_20deg.npy')
maxdivisor = dat_jun_20deg.shape[1]//2800
dat_jun_20deg = np.reshape(dat_jun_20deg[0:len(incSensors),0:maxdivisor*2800],(-1,2800,len(incSensors)))
for i in range(3):
  dat_jun_20deg[:,:,i] = (dat_jun_20deg[:,:,i]-means[i])/stddevs[i]
for i in range(30,40):
  stall_prob = process_utils.predict1d(data=dat_jun_20deg[i,:,:], model=myclassifier, windowsize=2800, sensorcount=len(incSensors))
  print ('Stall probability of June 20deg test point #{} = {}'.format(i*2800, stall_prob))


#%% For June2019-2 data standardized
myclassifier = load_model('/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/KerasFiles/06222019_training/UnfilteredData/06222019_StallOnly_96val_2800_3pzt_std.h5')
dataloc = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/StdTest_062419/'
incSensors = ('PZTLB','PZTLT','PZTRB')
means = [-0.0002862905522754296, 0.00014160949504295255, 2.983585730877926e-05, -36.33824690045131] # As obtained by training data
stddevs = [0.023828177361846174, 0.012151506564682033, 0.021041555452279762, 15.658515723288968] # As obtained by training data

dat_jun_2deg = np.load(dataloc+'7000_20ms_2deg.npy')
maxdivisor = dat_jun_2deg.shape[1]//2800
dat_jun_2deg = np.reshape(dat_jun_2deg[0:len(incSensors),0:maxdivisor*2800],(-1,2800,len(incSensors)))
for i in range(3):
  dat_jun_2deg[:,:,i] = (dat_jun_2deg[:,:,i]-means[i])/stddevs[i]
for i in range(0,10):
  stall_prob = process_utils.predict1d(data=dat_jun_2deg[i,:,:], model=myclassifier, windowsize=2800, sensorcount=len(incSensors))
  print ('Stall probability of June 2deg test point #{} = {}'.format(i*2800, stall_prob))

dat_jun_20deg = np.load(dataloc+'7000_20ms_20deg.npy')
maxdivisor = dat_jun_20deg.shape[1]//2800
dat_jun_20deg = np.reshape(dat_jun_20deg[0:len(incSensors),0:maxdivisor*2800],(-1,2800,len(incSensors)))
for i in range(3):
  dat_jun_20deg[:,:,i] = (dat_jun_20deg[:,:,i]-means[i])/stddevs[i]
for i in range(30,40):
  stall_prob = process_utils.predict1d(data=dat_jun_20deg[i,:,:], model=myclassifier, windowsize=2800, sensorcount=len(incSensors))
  print ('Stall probability of June 20deg test point #{} = {}'.format(i*2800, stall_prob))


#%% State estimation (using June2019-3 data standardized)
myclassifier = load_model('/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 2/KerasFiles/06222019_training/UnfilteredData/06222019_StateOnly_92val_2800_3pzt+SG_std.h5')
dataloc = '/Volumes/Google Drive File Stream/Shared drives/WindTunnelTests-Feb2019/Wind Tunnel Data 3/StdTestwSTRN_062619/'
incSensors = ('PZTLB','PZTLT','PZTRB','SG')
means = [-0.0002862905522754296, 0.00014160949504295255, 2.983585730877926e-05, -36.33824690045131] # As obtained by training data
stddevs = [0.023828177361846174, 0.012151506564682033, 0.021041555452279762, 15.658515723288968] # As obtained by training data

dat_jun_2deg = np.load(dataloc+'7000_20ms_2deg.npy')
maxdivisor = dat_jun_2deg.shape[1]//2800
dat_jun_2deg = np.reshape(dat_jun_2deg[0:len(incSensors),0:maxdivisor*2800],(-1,2800,len(incSensors)))
for i in range(4):
  dat_jun_2deg[:,:,i] = (dat_jun_2deg[:,:,i]-means[i])/stddevs[i]
for i in range(30,40):
  state_est = process_utils.predict1d_state(data=dat_jun_2deg[i,:,:], model=myclassifier, windowsize=2800, sensorcount=len(incSensors))
  print ('Estimated state of June 2deg test point #{} = {}'.format(i*2800, stateDict[state_est]))
#%%
