from multiprocessing import Queue
import sys, os
import math
import time
import copy
import numpy as np
import pandas as pd
import pathlib
sys.path.append(os.path.abspath('./helpers'))
sys.path.append(os.path.abspath('./fbf-vlm'))
import proc_keras_estimates_helper
import proc_MFCshape_helper
import proc_tempcomp_helper
import proc_vlm_estimates_helper
import constant as const
file_path = pathlib.Path(__file__).parent.absolute()


SSNSG_CTEvar_wing = dict()
SSNSG_CTEvar_wing = {1:109, 5:88, 6:43, 7:54, 9:55}

MFC_averages = dict()
MFC_averages["MFC1_SG5"] = (-427, -355, -284, -213, -142, -71, 0, 220, 470, 710, 910, 1090, 1250) #(-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6) camber (up, neutral, down)
MFC_averages["MFC1_SG6"] = (-500, -416, -333, -250, -166, -83, 0, 230, 550, 830, 1050, 1260, 1440) #(-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6)

class ProcEstimates:
  def __init__ (self, daq_samplerate, plot_refresh_rate, downsample_mult, models):
    self.daq_samplerate = daq_samplerate
    self.plot_refresh_rate = plot_refresh_rate
    self.downsample_mult = downsample_mult
    self.models = models

class ProcEstimatesRealtime (ProcEstimates):
  def __init__ (self, sensor_queue, estimates_queue, daq_samplerate, plot_refresh_rate, downsample_mult, use_compensated_strains, keras_est, mfc_est, liftdrag_est, mfc_est_meth='simple', liftdrag_est_meth='vlm', models=None, keras_samplesize=None):
    super().__init__(daq_samplerate, plot_refresh_rate, downsample_mult, models)
    if use_compensated_strains:
      raise NotImplementedError("Using compensated strains in real-time is not implemented yet") #TODO
    if keras_est:
      self.keras_estimator = proc_keras_estimates_helper.iFlyNetEstimates(keras_samplesize, models) #Initialize Keras estimates if this is not running in realtime
    if mfc_est:
      if mfc_est_meth == 'full':
        self.mfc_estimator = proc_MFCshape_helper.CalcMFCShape()
    
    self.keras_est = keras_est
    self.mfc_est = mfc_est
    self.liftdrag_est = liftdrag_est
    self.sensor_queue = sensor_queue
    self.estimates_queue = estimates_queue
    self.keras_samplesize = keras_samplesize
    self.mfc_est_meth = mfc_est_meth
    self.liftdrag_est = liftdrag_est
    self.liftdrag_est_meth = liftdrag_est_meth

  def prepare_data(self):
    while True:
      try:
        sensor_data = self.sensor_queue.get_nowait()
        self.reduced_sensor_data = np.take(sensor_data, range(int(sensor_data.shape[1]//2 - self.keras_samplesize/2), int(sensor_data.shape[1]//2 + self.keras_samplesize/2)), axis=1)
        self.sensor_data_keras = list()
        for sensorcut in self.models['activesensors']:
          self.sensor_data_keras.append(self.reduced_sensor_data[np.array(sensorcut),:])
      except:
        pass
      time.sleep(self.plot_refresh_rate/3)

  def estimate_stall(self):
    if self.keras_est is False:
      raise Exception("You declared you won't do Keras estimations, but asking it here")
    while True:
      try:
        stall_estimates = self.keras_estimator.estimate_stall(self.sensor_data_keras[0])
        self.estimates_queue[0].put_nowait(stall_estimates.reshape(1,1))
        time.sleep(self.plot_refresh_rate/3)
      except:
        pass
    
  def estimate_state(self):
    if self.keras_est is False:
      raise Exception("You declared you won't do Keras estimations, but asking it here")
    while True:
      try:
        state_estimates = self.keras_estimator.estimate_state(self.sensor_data_keras[2])
        self.estimates_queue[1].put_nowait(state_estimates.T)
        time.sleep(self.plot_refresh_rate/3)
      except:
        pass

  def estimate_mfc(self):
    if self.mfc_est is False:
      raise Exception("You declared you won't do MFC estimations, but asking it here")
    while True:
      try:
        if self.mfc_est_meth == 'full':
          self.mfc_estimator.estimate_shape_analytic(self.reduced_sensor_data, self.estimates_queue[3]) #Number of estimates is driven by plot refresh rate (even if there are more predictions by Keras)
          #!!!Shape of above could be wrong. Make sure it is (2,1)

        elif self.mfc_est_meth == 'simple':
          #Simplified MFC shape estimates within the range (-6,+6) for MFC1 and MFC2. 
          
          mfc1_data = self.reduced_sensor_data[10:12,:] #SG5, SG6
          mfc2_data = self.reduced_sensor_data[12:14,:] #SG7, SG9
          relevant_mfc1_data = np.mean (mfc1_data, axis=1)

          closest_mfc1_sg5_val = min(MFC_averages["MFC1_SG5"], key=lambda x:abs(x-relevant_mfc1_data[0]))
          closest_mfc1_sg6_val = min(MFC_averages["MFC1_SG6"], key=lambda x:abs(x-relevant_mfc1_data[1]))
          closest_mfc1_sg5 = MFC_averages["MFC1_SG5"].index(closest_mfc1_sg5_val) - 6 #-6 is here to normalize index.
          closest_mfc1_sg6 = MFC_averages["MFC1_SG6"].index(closest_mfc1_sg6_val) - 6 #-6 is here to normalize index.
          closest_mfc1 = int((closest_mfc1_sg5 + closest_mfc1_sg6)/2)
          closest_mfc2 = 0 #(MFC2 not working)
          
          pretty_mfc_ests = np.array([[closest_mfc1],[closest_mfc2]])
          self.estimates_queue[3].put_nowait(pretty_mfc_ests)
        time.sleep(self.plot_refresh_rate/3)
      except:
        pass
  
  def estimate_liftdrag(self):
    if self.liftdrag_est is False:
      raise Exception("You declared you won't do Lift/Drag estimations, but asking it here")
    while True:
      try:
        if self.liftdrag_est_meth == '1dcnn':
          liftdrag_estimates = self.keras_estimator.estimate_liftdrag(self.sensor_data_keras[1])
          pretty_liftdrag_estimates = np.array([[liftdrag_estimates[0,0]],[liftdrag_estimates[0,1]]])
          self.estimates_queue[2].put_nowait(pretty_liftdrag_estimates)


        elif self.liftdrag_est_meth == 'vlm':
          liftdrag_dict = dict()

          state_ests = self.estimates_queue[1].get_nowait()
          airspeed, aoa = state_ests[1,0], state_ests[0,0]
          self.estimates_queue[1].put_nowait(np.array([[airspeed],[aoa]]))
          mfc_ests = self.estimates_queue[3].get_nowait()
          mfc1, mfc2 = mfc_ests[1,0], mfc_ests[0,0]
          self.estimates_queue[3].put_nowait(np.array([[mfc1],[mfc2]]))

          est_lift, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(airspeed), int(aoa), int(mfc1), int(mfc2)) #V, aoa, mfc1, mfc2
          pretty_liftdrag_estimates = np.array([[est_lift],[est_drag_i]])
          self.estimates_queue[2].put_nowait(pretty_liftdrag_estimates)


        elif self.liftdrag_est_meth == 'sg1+vlm':
          liftdrag_dict = dict()

          state_ests = self.estimates_queue[1].get_nowait()
          airspeed, aoa = state_ests[1,0], state_ests[0,0]
          self.estimates_queue[1].put_nowait(np.array([[airspeed],[aoa]]))
          mfc_ests = self.estimates_queue[3].get_nowait()
          mfc1, mfc2 = mfc_ests[1,0], mfc_ests[0,0]
          self.estimates_queue[3].put_nowait(np.array([[mfc1],[mfc2]]))

          midpoint = self.reduced_sensor_data[6].shape[0]/2
          step_size = self.reduced_sensor_data[6].shape[0]/6
          est_lift = -1 * np.mean(self.reduced_sensor_data[6, int(midpoint-step_size) : int(midpoint+step_size)])
          _, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(airspeed), int(aoa), int(mfc1), int(mfc2)) #V, aoa, mfc1, mfc2
          pretty_liftdrag_estimates = np.array([[est_lift],[est_drag_i]])
          self.estimates_queue[2].put_nowait(pretty_liftdrag_estimates)


        elif self.liftdrag_est_meth == 'sg1+vlm_v2':
          liftdrag_dict = dict()
          self.SG1_hist_filtered = list()
          self.aoa_hist = list()
          self.liftdrag_hist = list()

          state_ests = self.estimates_queue[1].get_nowait()
          airspeed, aoa = state_ests[1,0], state_ests[0,0]
          self.estimates_queue[1].put_nowait(np.array([[airspeed],[aoa]]))
          mfc_ests = self.estimates_queue[3].get_nowait()
          mfc1, mfc2 = mfc_ests[1,0], mfc_ests[0,0]
          self.estimates_queue[3].put_nowait(np.array([[mfc1],[mfc2]]))
          self.aoa_hist.append(aoa)

          midpoint = self.reduced_sensor_data[6].shape[0]/2
          step_size = self.reduced_sensor_data[6].shape[0]/6
          curr_SG1_filtered = np.mean(self.reduced_sensor_data[6, int(midpoint-step_size) : int(midpoint+step_size)])
          self.SG1_hist_filtered.append(curr_SG1_filtered)

          stall_estimate = self.estimates_queue[0].get_nowait()[0,0]
          self.estimates_queue[0].put_nowait(stall_estimate.reshape(1,1))

          try:
            liftdrag_ests = self.estimates_queue[2].get_nowait()
            lift, drag = liftdrag_ests[0,0], liftdrag_ests[1,0]
            self.estimates_queue[2].put_nowait(np.array([[lift],[drag]]))
          except:
            lift, drag = 0, 0
          self.liftdrag_hist.append([lift,drag])

          if stall_estimate == True:
            SG1_lift_prev_stp = -1 * self.SG1_hist_filtered[-2] * np.cos(np.radians(int(self.aoa_hist[-2])))
            SG1_lift_curr_stp = -1 * self.SG1_hist_filtered[-1] * np.cos(np.radians(int(self.aoa_hist[-1])))
            lift_prev_stp = self.liftdrag_hist[-2][0]
            SG1_pct_chg = (SG1_lift_curr_stp - SG1_lift_prev_stp)/SG1_lift_prev_stp*100*2.5 #2.5 here is correction to account for the location difference of SG1 and commSG (elliptic lift profile assumed)
            _, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(airspeed), int(aoa), int(mfc1), int(mfc2)) #V, aoa, mfc1, mfc2
            est_lift = lift_prev_stp * (1+SG1_pct_chg/100)
          else:
            est_lift, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(airspeed), int(aoa), int(mfc1), int(mfc2)) #V, aoa, mfc1, mfc2
          pretty_liftdrag_estimates = np.array([[est_lift],[est_drag_i]])
          self.estimates_queue[2].put_nowait(pretty_liftdrag_estimates)

        time.sleep(self.plot_refresh_rate/3)
      except:
        pass



class ProcEstimatesOffline (ProcEstimates):
  def __init__ (self, input_data, daq_samplerate, plot_refresh_rate, downsample_mult, use_compensated_strains, models=None, keras_samplesize=None):
    super().__init__(daq_samplerate, plot_refresh_rate, downsample_mult, models)
    
    sensor_data = copy.copy(input_data)
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
    #Slicing the data
    ###
    if models == None: #No Keras estimations (only MFC estimates)
      self.num_estimates = math.floor(sensor_data.shape[1]/daq_samplerate/plot_refresh_rate) #Number of estimates is driven by plot refresh rate.
      self.reduced_sensor_data = sensor_data
    else:
      self.keras_samplesize = keras_samplesize
      self.num_estimates = math.floor(sensor_data.shape[1]/keras_samplesize) #Number of estimates is driven by Keras expectations.
      self.reduced_sensor_data = sensor_data [:,0:keras_samplesize*self.num_estimates]
      self.sensor_data_keras = list()
      for sensorcut in models['activesensors']:
        self.sensor_data_keras.append(self.reduced_sensor_data[np.array(sensorcut),:])
    self.step_size = int (self.reduced_sensor_data.shape[1]/self.num_estimates)

    self.sensor_data = sensor_data

  ###
  #General function for making the Estimations
  ###
  def make_estimates(self, keras_est, mfc_est, liftdrag_est, mfc_est_meth='simple', liftdrag_est_meth='vlm'):
    #Stall and state estimates from Keras
    if keras_est:
      keras_estimator = proc_keras_estimates_helper.iFlyNetEstimates(self.keras_samplesize, self.models) #Initialize Keras estimates if this is not running in realtime
      self.stall_estimates = keras_estimator.estimate_stall(self.sensor_data_keras[0]) #Number of estimates is driven by Keras expectations.
      self.state_estimates = keras_estimator.estimate_state(self.sensor_data_keras[2]) #Number of estimates is driven by Keras expectations.

    #MFC shape estimation
    #Analytic MFC full shape estimates. 
    if mfc_est:
      if mfc_est_meth == 'full':
        self.mfc_estimates = list()
        mfc_estimator = proc_MFCshape_helper.CalcMFCShape()
        shape_queue = Queue()
        
        for i in range(self.num_estimates):
          mfc_estimator.estimate_shape_analytic(self.reduced_sensor_data[:,i*self.step_size:i*self.step_size+10], shape_queue) #Number of estimates is driven by plot refresh rate (even if there are more predictions by Keras)
          self.mfc_estimates.append(shape_queue.get())

      elif mfc_est_meth == 'simple':
        #Simplified MFC shape estimates within the range (-6,+6) for MFC1 and MFC2. 
        self.mfc_estimates = np.zeros((self.num_estimates, 2))
        mfc1_data = self.reduced_sensor_data[10:12,:] #SG5, SG6
        mfc2_data = self.reduced_sensor_data[12:14,:] #SG7, SG9
        
        for i in range(self.num_estimates):
          relevant_mfc1_data = np.mean (mfc1_data[:,i*self.step_size:i*self.step_size+10], axis=1)
          relevant_mfc2_data = np.mean (mfc2_data[:,i*self.step_size:i*self.step_size+10], axis=1)

          closest_mfc1_sg5_val = min(MFC_averages["MFC1_SG5"], key=lambda x:abs(x-relevant_mfc1_data[0]))
          closest_mfc1_sg6_val = min(MFC_averages["MFC1_SG6"], key=lambda x:abs(x-relevant_mfc1_data[1]))
          closest_mfc1_sg5 = MFC_averages["MFC1_SG5"].index(closest_mfc1_sg5_val) - 6 #-6 is here to normalize index.
          closest_mfc1_sg6 = MFC_averages["MFC1_SG6"].index(closest_mfc1_sg6_val) - 6 #-6 is here to normalize index.
          closest_mfc1 = int((closest_mfc1_sg5 + closest_mfc1_sg6)/2)
          closest_mfc2 = 0 #(MFC2 not working)
          
          self.mfc_estimates[i,0] = closest_mfc1
          self.mfc_estimates[i,1] = closest_mfc2

    #Lift and drag estimations based on AoA, airspeed, MFC estimates via VLM
    if liftdrag_est:
      if liftdrag_est_meth == 'vlm':
        self.liftdrag_estimates = np.zeros((self.num_estimates,2))
        liftdrag_dict = dict()

        for i in range(self.num_estimates):
          est_lift, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(self.state_estimates[i,0]), int(self.state_estimates[i,1]), int(self.mfc_estimates[i,0]), int(self.mfc_estimates[i,1])) #V, aoa, mfc1, mfc2
          self.liftdrag_estimates[i,0] = est_lift
          self.liftdrag_estimates[i,1] = est_drag_i
      

      elif liftdrag_est_meth == '1dcnn':
        self.liftdrag_estimates = keras_estimator.estimate_liftdrag(self.sensor_data_keras[1])


      elif liftdrag_est_meth == 'sg1+vlm':
        step_size = int (self.reduced_sensor_data.shape[1]/self.num_estimates)
        self.liftdrag_estimates = np.zeros((self.num_estimates,2))
        liftdrag_dict = dict()

        for i in range(self.num_estimates):
          est_lift = -1 * np.mean(self.reduced_sensor_data[6, int((i)*step_size-step_size/6) : int((i)*step_size+step_size/6)])
          _, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(self.state_estimates[i,0]), int(self.state_estimates[i,1]), int(self.mfc_estimates[i,0]), int(self.mfc_estimates[i,1])) #V, aoa, mfc1, mfc2
          self.liftdrag_estimates[i,0] = est_lift
          self.liftdrag_estimates[i,1] = est_drag_i


      elif liftdrag_est_meth == 'sg1+vlm_v2':
        step_size = int (self.reduced_sensor_data.shape[1]/self.num_estimates)
        self.liftdrag_estimates = np.zeros((self.num_estimates,2))
        liftdrag_dict = dict()

        if not hasattr(self, "stall_estimates"):
          raise Exception("Stall estimates are required for this method.")

        for i in range(self.num_estimates):
          if self.stall_estimates[i] == True:
            SG1_lift_prev_stp = -1 * np.mean(self.reduced_sensor_data[6, int((i-1)*step_size-step_size/6) : int((i-1)*step_size+step_size/6)]) * np.cos(np.radians(int(self.state_estimates[i-1,1])))
            SG1_lift_curr_stp = -1 * np.mean(self.reduced_sensor_data[6, int((i)*step_size-step_size/6) : int((i)*step_size+step_size/6)]) * np.cos(np.radians(int(self.state_estimates[i,1])))
            lift_prev_stp = self.liftdrag_estimates[i-1,0]
            SG1_pct_chg = (SG1_lift_curr_stp - SG1_lift_prev_stp)/SG1_lift_prev_stp*100*2.5 #2.5 here is correction to account for the location difference of SG1 and commSG (elliptic lift profile assumed)
            est_lift, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(self.state_estimates[i,0]), int(self.state_estimates[i,1]), int(self.mfc_estimates[i,0]), int(self.mfc_estimates[i,1])) #V, aoa, mfc1, mfc2
            est_lift = lift_prev_stp * (1+SG1_pct_chg/100)
          else:
            est_lift, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(self.state_estimates[i,0]), int(self.state_estimates[i,1]), int(self.mfc_estimates[i,0]), int(self.mfc_estimates[i,1])) #V, aoa, mfc1, mfc2  

          self.liftdrag_estimates[i,0] = est_lift
          self.liftdrag_estimates[i,1] = est_drag_i


      elif liftdrag_est_meth == 'sg1+vlm_v2+xfoil':
        step_size = int (self.reduced_sensor_data.shape[1]/self.num_estimates)
        self.liftdrag_estimates = np.zeros((self.num_estimates,2))
        liftdrag_dict = dict()
        parasiticdrag_dict = dict()

        if not hasattr(self, "stall_estimates"):
          raise Exception("Stall estimates are required for this method.")

        try:
          airfoil = const.AIRFOIL_BASE.replace(" ", "")
          cdp_file_path = os.path.join(file_path.parent, 'assets', airfoil+'_CDp.csv')
          cdp_data = pd.read_csv(cdp_file_path, delim_whitespace=True)
          
          parasiticdrag_dict[0] = dict()
          parasiticdrag_dict[0][0] = 0
          for cnt, speed in enumerate(cdp_data['Speed']):
            parasiticdrag_dict[speed] = dict()
            for cnt2, cdp in enumerate(cdp_data.iloc[cnt]):
              if cnt2 > 0:
                aoa = int(cdp_data.columns[cnt2])
                parasiticdrag_dict[speed][aoa] = (cdp_data.iloc[cnt][cnt2]*1.5) * 1/2 * const.RHO * speed**2 * const.CHORD * const.SPAN #*1.5 is correction for frictional drag contribution
        except:
          raise Exception("Problem in getting parasitic drag.")

        for i in range(self.num_estimates):
          if self.stall_estimates[i] == True:
            SG1_lift_prev_stp = -1 * np.mean(self.reduced_sensor_data[6, int((i-1)*step_size-step_size/6) : int((i-1)*step_size+step_size/6)]) * np.cos(np.radians(int(self.state_estimates[i-1,1])))
            SG1_lift_curr_stp = -1 * np.mean(self.reduced_sensor_data[6, int((i)*step_size-step_size/6) : int((i)*step_size+step_size/6)]) * np.cos(np.radians(int(self.state_estimates[i,1])))
            lift_prev_stp = self.liftdrag_estimates[i-1,0]
            SG1_pct_chg = (SG1_lift_curr_stp - SG1_lift_prev_stp)/SG1_lift_prev_stp*100*2.5 #2.5 here is correction to account for the location difference of SG1 and commSG (elliptic lift profile assumed)
            est_lift, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(self.state_estimates[i,0]), int(self.state_estimates[i,1]), int(self.mfc_estimates[i,0]), int(self.mfc_estimates[i,1])) #V, aoa, mfc1, mfc2
            est_lift = lift_prev_stp * (1+SG1_pct_chg/100)
            est_drag_p = parasiticdrag_dict[int(self.state_estimates[i,0])] [int(self.state_estimates[i,1])]
          else:
            est_lift, est_drag_i, liftdrag_dict = proc_vlm_estimates_helper.get_liftANDdrag(liftdrag_dict, int(self.state_estimates[i,0]), int(self.state_estimates[i,1]), int(self.mfc_estimates[i,0]), int(self.mfc_estimates[i,1])) #V, aoa, mfc1, mfc2  
            est_drag_p = parasiticdrag_dict[int(self.state_estimates[i,0])] [int(self.state_estimates[i,1])]

          self.liftdrag_estimates[i,0] = est_lift
          self.liftdrag_estimates[i,1] = est_drag_i + est_drag_p