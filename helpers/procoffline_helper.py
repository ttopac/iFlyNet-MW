from multiprocessing import Queue
import sys, os
import math
import numpy as np
sys.path.append(os.path.abspath('./helpers'))
import proc_keras_estimates_helper
import proc_MFCshape_helper

class ProcEstimatesOffline:
  def __init__ (self, sensor_data, daq_samplerate, plot_refresh_rate, downsample_mult, use_compensated_strains, models=None, keras_samplesize=None):
    self.daq_samplerate = daq_samplerate
    self.plot_refresh_rate = plot_refresh_rate
    self.downsample_mult = downsample_mult
    self.use_compensated_strains = use_compensated_strains
    self.models = models
    
    if models != None: #There's also Keras predictions
      self.keras_samplesize = keras_samplesize
      num_estimates = math.floor(sensor_data.shape[1]/keras_samplesize)
      reduced_sensor_data = sensor_data [:,0:keras_samplesize*num_estimates]
      self.sensor_data_keras = list()
      for sensorcut in models['sensorcuts']:
        if sensorcut != 0: #PZT + SG
          self.sensor_data_keras.append(np.concatenate ((reduced_sensor_data[0:6], reduced_sensor_data[sensorcut:]), axis=0))
        else: #PZTonly
          self.sensor_data_keras.append(reduced_sensor_data[0:6])

    else:
      num_estimates = math.floor(sensor_data.shape[1]/daq_samplerate/plot_refresh_rate) 
      reduced_sensor_data = sensor_data [:,0:int(daq_samplerate*plot_refresh_rate*num_estimates)]
    
    self.sensor_data_MFCest = reduced_sensor_data #IF PZT+commSG DATA TO BE USED

  def make_estimates(self):
    if self.models != None:
      keras_estimator = proc_keras_estimates_helper.iFlyNetEstimates(self.keras_samplesize, self.models) #Initialize Keras estimates if this is not running in realtime
      self.stall_estimates = keras_estimator.estimate_stall(self.sensor_data_keras[0])
      self.liftdrag_estimates = keras_estimator.estimate_liftdrag(self.sensor_data_keras[1])
      self.stall_estimates = self.stall_estimates[0::int(self.daq_samplerate/self.keras_samplesize*self.plot_refresh_rate)]
      self.liftdrag_estimates = self.liftdrag_estimates[0::int(self.daq_samplerate/self.keras_samplesize*self.plot_refresh_rate)]

    self.mfc_estimates = list()
    mfc_estimator = proc_MFCshape_helper.CalcMFCShape()
    shape_queue = Queue()
    datasize = self.sensor_data_MFCest.shape[1]
    
    i = 0
    while i < datasize:
      mfc_estimator.estimate_shape_analytic(self.sensor_data_MFCest[:,i:i+10], shape_queue)
      self.mfc_estimates.append(shape_queue.get())
      i += int(self.daq_samplerate*self.plot_refresh_rate)
    self.mfc_estimates.insert(0,np.zeros_like(self.mfc_estimates[0]))