from multiprocessing import Queue
import sys, os
import math
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
MFC_averages["MFC1_SG5"] = (-528, -421, -312, -210, -120, -51, 0, 165, 403, 629, 837, 1022, 1189) #(-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6) camber (up, neutral, down)
MFC_averages["MFC1_SG6"] = (-642, -492, -360, -244, -135, -56, 0, 194, 477, 742, 980, 1187, 1373) #(-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6)

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