from multiprocessing import Queue
import sys, os
import math
import numpy as np
sys.path.append(os.path.abspath('./helpers'))
import proc_keras_estimates_helper
import proc_MFCshape_helper
import proc_tempcomp_helper

SSNSG_CTEvar_wing = dict()
SSNSG_CTEvar_wing = {1:109, 5:88, 6:43, 7:54, 9:55}

class ProcEstimatesOffline:
  def __init__ (self, sensor_data, daq_samplerate, plot_refresh_rate, downsample_mult, use_compensated_strains, models=None, keras_samplesize=None):
    self.daq_samplerate = daq_samplerate
    self.plot_refresh_rate = plot_refresh_rate
    self.downsample_mult = downsample_mult
    self.models = models
    self.test_duration = int(sensor_data.shape[1]/daq_samplerate)
    self.pred_count = int(sensor_data.shape[1]/downsample_mult)
    
    ###
    #Temperature compensation
    ###
    if use_compensated_strains:
      ref_temp_SG1 = sensor_data[16][0]
      ref_temp_wing = sensor_data[17][0]

    #Temp comp of SSN SGs
    compSSNSGs = dict()
    SSNSG_temp_comp = proc_tempcomp_helper.SSNSG_Temp_Comp(ref_temp_SG1, ref_temp_wing)
    compSSNSGs[1] = SSNSG_temp_comp.compensate(sensor_data[6,:], sensor_data[16,:], 'SG1', SSNSG_CTEvar_wing[1]) #SG 1 is here.
    for cnt, sg in enumerate([5, 6, 7 ,9]):
      compSSNSGs[sg] = SSNSG_temp_comp.compensate(sensor_data[cnt+10,:], sensor_data[17,:], 'MFC', SSNSG_CTEvar_wing[sg]) #SG 5, 6, 7, 9 are here.
    #Temp comp of Commercial SGs
    commSG_temp_comp = proc_tempcomp_helper.CommSG_Temp_Comp(ref_temp_SG1, ref_temp_wing)
    comp_commSG, _ = commSG_temp_comp.compensate(sensor_data[14:16,:], sensor_data[17,:], 'rod', 0)
    #Replace the SG data with compensated data
    sensor_data[6,:] = compSSNSGs[1]
    for cnt, sg in enumerate([5, 6, 7 ,9]):
      sensor_data[cnt+10,:] = compSSNSGs[sg]
    sensor_data[14:16,:] = comp_commSG


    ###
    #Slice the data
    ###
    if models == None: #No Keras estimations (only MFC estimates)
      num_estimates = math.floor(sensor_data.shape[1]/daq_samplerate/plot_refresh_rate) #Number of estimates is driven by plot refresh rate.
      self.reduced_sensor_data = sensor_data [:,0:int(daq_samplerate*plot_refresh_rate*num_estimates)]
    else:
      self.keras_samplesize = keras_samplesize
      num_estimates = math.floor(sensor_data.shape[1]/keras_samplesize) #Number of estimates is driven by Keras expectations.
      self.reduced_sensor_data = sensor_data [:,0:keras_samplesize*num_estimates]
      self.sensor_data_keras = list()
      for sensorcut in models['activesensors']:
        self.sensor_data_keras.append(self.reduced_sensor_data[np.array(sensorcut),:])
    

  def make_estimates(self):
    if self.models != None:
      #Keras estimates.
      keras_estimator = proc_keras_estimates_helper.iFlyNetEstimates(self.keras_samplesize, self.models) #Initialize Keras estimates if this is not running in realtime
      self.stall_estimates = keras_estimator.estimate_stall(self.sensor_data_keras[0]) #Number of estimates is driven by Keras expectations.
      self.liftdrag_estimates = keras_estimator.estimate_liftdrag(self.sensor_data_keras[1]) #Number of estimates is driven by Keras expectations.
      self.state_estimates = keras_estimator.estimate_state(self.sensor_data_keras[2]) #Number of estimates is driven by Keras expectations.

    #Analytic MFC estimates. 
    self.mfc_estimates = list()
    mfc_estimator = proc_MFCshape_helper.CalcMFCShape()
    shape_queue = Queue()
    datasize = self.reduced_sensor_data.shape[1]
    
    i = 0
    while i < datasize:
      mfc_estimator.estimate_shape_analytic(self.reduced_sensor_data[:,i:i+10], shape_queue) #Number of estimates is driven by plot refresh rate (even if there are more predictions by Keras)
      self.mfc_estimates.append(shape_queue.get())
      i += int(self.daq_samplerate*self.plot_refresh_rate)
