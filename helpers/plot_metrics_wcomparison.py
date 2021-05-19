import matplotlib as mpl
import matplotlib.pyplot as plt
import time
import numpy as np
import sys, os

sys.path.append(os.path.abspath('./helpers'))
import proc_tempcomp_helper

class PlotsWComparison:
  def __init__(self, pred_freq, ongui, offline):
    self.pred_freq = pred_freq
    self.ongui = ongui
    self.offline = offline

  def init_realtime_params (self, visible_duration, downsample_mult, params, plot_refresh_rate):
    self.visible_duration = visible_duration
    self.downsample_mult = downsample_mult
    self.params = params
    self.plot_refresh_rate = plot_refresh_rate
    # self.xs = np.linspace (0, self.visible_duration, int(self.visible_duration/self.plot_refresh_rate))
    # self.ys = np.zeros((2,int(self.visible_duration/self.plot_refresh_rate)))
    self.xs = np.zeros(1)
    self.ys = np.zeros((2,1))

  def init_common_params (self, y_label):
    mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
    mpl.rcParams['axes.edgecolor'] = 'black'
    mpl.rcParams['axes.linewidth'] = 1
    
    self.fig = plt.figure()
    self.ax1 = self.fig.add_subplot(1,1,1)
    self.ax1.set_xlabel("Time", labelpad=2, fontsize=11)
    self.ax1.set_ylabel(y_label, labelpad=2, fontsize=11) #Commented out for simplification. We are showing trends, not absolute values.
    self.ax1.grid(False)

  def term_common_params (self, legend):
    if legend:
      lns=list((self.meas_line, self.est_line))
      lbls = [l.get_label() for l in lns]
      self.leg1 = self.ax1.legend(lns, lbls, fontsize=9, loc="upper right", ncol=1, columnspacing=1)
      
      for line in self.leg1.get_lines():
        line.set_linewidth(1.5)
        line.set_markersize(1.5)
    
    if self.ongui:
      self.fig.set_size_inches(3.5, 3.0) #width, height
      plt.tight_layout()

  def plot_live(self, i, meas_line, est_line, meas_queue, est_queue, start_time, plot_name, use_compensated_strains=False, temp_queue=None):
    #Here meas_queue and est_queue contains lists of shape (plot_time/plot_refresh_rate,). This is (3000,) for 300 seconds of data at 10 hz.
    t0 = time.time()
    cur_frame = abs(int((t0-start_time)/self.plot_refresh_rate))
    
    meas_data = meas_queue[cur_frame]
    est_data = est_queue[cur_frame]
    
    if plot_name == 'lift' or plot_name == 'drag':
      temp_data = temp_queue[cur_frame]
      if i == 0: #Set initial temperature at the beginning
        self.ref_temp_SG1 = temp_data[0]
        self.ref_temp_wing = temp_data[1]
      if use_compensated_strains:
        meas_temp_comp = proc_tempcomp_helper.CommSG_Temp_Comp(self.ref_temp_SG1, self.ref_temp_wing)
        meas_data, _ = meas_temp_comp.compensate(meas_data, temp_data[1], 'rod', 0)
    
    if (i%int(self.visible_duration/self.plot_refresh_rate) == 0): #Reset data once the period is filled.
      self.xs = np.zeros(1)
      self.ys = np.array([[meas_data], [est_data]])

    self.xs = np.append(self.xs, i%int(self.visible_duration/self.plot_refresh_rate) * self.plot_refresh_rate)
    self.ys = np.append(self.ys, np.zeros((2,1)), axis=1)
    self.ys[0,-1] = meas_data
    self.ys[1,-1] = est_data
    
    meas_line.set_xdata(self.xs)
    est_line.set_xdata(self.xs)
    if plot_name == 'lift' or plot_name=='drag':
      meas_line.set_ydata(-self.ys[0])
    else:
      meas_line.set_ydata(self.ys[0])
    est_line.set_ydata(self.ys[1])

    return meas_line, est_line


class AirspeedPlot (PlotsWComparison):
  def __init__(self, pred_sample_size, ongui, offline):
    super().__init__(pred_sample_size, ongui, offline)
  def init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate):
    super().init_realtime_params(visible_duration, downsample_mult, params, plot_refresh_rate) 
  def init_common_params(self, y_label):
    super().init_common_params(y_label)
  def term_common_params(self, legend):
    super().term_common_params(legend)

  def plot_airspeed_wcomparison(self):
    if self.ongui:
      self.num_samples = int(self.params["sample_rate"]*self.plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_xlim(-2, self.visible_duration+2)
      self.ax1.set_ylim(-2, 22) #This scale is m/s
      self.ax1.set_xticklabels([])
      self.meas_line, = self.ax1.plot(self.xs, self.ys[0], linewidth=1.5, animated=True, label="Measured") 
      self.est_line, = self.ax1.plot(self.xs, self.ys[1], linewidth=1.5, animated=True, label="Predicted")

  def plot_airspeed_live(self, i, vel_meas_queue, vel_est_queue, start_time):
    vel_meas_queue = np.asarray(vel_meas_queue)
    vel_est_queue = np.asarray(vel_est_queue)[:,0]
    self.meas_line, self.est_line = super().plot_live(i, self.meas_line, self.est_line, vel_meas_queue, vel_est_queue, start_time, 'airspeed')
    return list((self.meas_line, self.est_line))
    

class AoaPlot (PlotsWComparison):
  def __init__(self, pred_sample_size, ongui, offline):
    super().__init__(pred_sample_size, ongui, offline)
  def init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate):
    super().init_realtime_params(visible_duration, downsample_mult, params, plot_refresh_rate) 
  def init_common_params(self, y_label):
    super().init_common_params(y_label)
  def term_common_params(self, legend):
    super().term_common_params(legend)

  def plot_aoa_wcomparison(self):
    if self.ongui:
      self.num_samples = int(self.params["sample_rate"]*self.plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_xlim(-2, self.visible_duration+2)
      self.ax1.set_ylim(-2, 22) #This scale is degrees
      self.ax1.set_xticklabels([])
      self.meas_line, = self.ax1.plot(self.xs, self.ys[0], linewidth=1.5, animated=True, label="Measured") 
      self.est_line, = self.ax1.plot(self.xs, self.ys[1], linewidth=1.5, animated=True, label="Predicted")

  def plot_aoa_live(self, i, aoa_meas_queue, est_queue, start_time):
    aoa_meas_queue = np.asarray(aoa_meas_queue)
    aoa_est_queue = np.asarray(est_queue)[:,1]
    self.meas_line, self.est_line = super().plot_live(i, self.meas_line, self.est_line, aoa_meas_queue, aoa_est_queue, start_time, 'aoa')
    return list((self.meas_line, self.est_line))


class LiftPlot (PlotsWComparison):
  def __init__(self, pred_sample_size, ongui, offline):
    super().__init__(pred_sample_size, ongui, offline)
  def init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate):
    super().init_realtime_params(visible_duration, downsample_mult, params, plot_refresh_rate) 
  def init_common_params(self, y_label):
    super().init_common_params(y_label)
  def term_common_params(self, legend):
    super().term_common_params(legend)

  def plot_lift_wcomparison(self, liftdrag_estimate_meth):
    if self.ongui:
      self.num_samples = int(self.params["sample_rate"]*self.plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_xlim(-2, self.visible_duration+2)
      self.ax1.set_xticklabels([])
  
      self.twin_ax = self.ax1.twinx()
      self.meas_line, = self.twin_ax.plot(self.xs, self.ys[0], linewidth=1.5, animated=True, label="Measured") 
      self.est_line, = self.ax1.plot(self.xs, self.ys[1], linewidth=1.5, animated=True, label="Predicted", color='#ff7f0e')

      if liftdrag_estimate_meth == '1dcnn':
        self.ax1.set_ylim (-30, 300) #This scale is microstrains
      elif liftdrag_estimate_meth == 'vlm' or liftdrag_estimate_meth == 'sg1+vlm_v2':
        self.ax1.set_ylim (-1.11, 11.1) #This scale is Newtons
      elif liftdrag_estimate_meth == 'sg1+vlm':
        self.ax1.set_ylim (-24, 240) #This scale is microstrains
      
      self.ax1.yaxis.set_major_locator(plt.MaxNLocator(6))
      self.twin_ax.set_xlim (-2, self.visible_duration+2)
      self.twin_ax.set_ylim(-30, 300) #This scale is microstrains
      self.twin_ax.set_yticklabels([])
  
  def plot_lift_live(self, i, data_queue, aoa_meas_queue, liftdrag_est_queue, use_compensated_strains, start_time):
    aoa_meas = np.asarray(aoa_meas_queue)+1.75
    # lift_meas_queue = np.asarray(data_queue)[:,14] #Without correcting for SG rotation.
    lift_meas_queue = np.asarray(data_queue)[:,14] * np.cos(np.radians(aoa_meas)) - np.asarray(data_queue)[:,15] * np.sin(np.radians(aoa_meas))
    lift_est_queue = np.asarray(liftdrag_est_queue)[:,0]
    temp_queue = np.asarray(data_queue)[:,16:18]
    self.meas_line, self.est_line = super().plot_live(i, self.meas_line, self.est_line, lift_meas_queue, lift_est_queue, start_time, 'lift', use_compensated_strains, temp_queue)
    return list((self.meas_line, self.est_line))


class DragPlot (PlotsWComparison):
  def __init__(self, pred_sample_size, ongui, offline):
    super().__init__(pred_sample_size, ongui, offline)
  def init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate):
    super().init_realtime_params(visible_duration, downsample_mult, params, plot_refresh_rate) 
  def init_common_params(self, y_label):
    super().init_common_params(y_label)
  def term_common_params(self, legend):
    super().term_common_params(legend)

  def plot_drag_wcomparison(self, liftdrag_estimate_meth):
    if self.ongui:
      self.num_samples = int(self.params["sample_rate"]*self.plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_xlim(-2, self.visible_duration+2)
      self.ax1.set_xticklabels([])

      self.twin_ax = self.ax1.twinx()
      self.meas_line, = self.twin_ax.plot(self.xs, self.ys[0], animated=True, label="Measured") 
      self.est_line, = self.ax1.plot(self.xs, self.ys[1], animated=True, label="Predicted", color='#ff7f0e')
      
      self.ax1.set_xlim (-2, self.visible_duration+2) 
      if liftdrag_estimate_meth == '1dcnn':
        self.ax1.set_ylim (-30, 300) #This scale is microstrains
      elif liftdrag_estimate_meth == 'vlm' or liftdrag_estimate_meth == 'sg1+vlm' or liftdrag_estimate_meth == 'sg1+vlm_v2':
        self.ax1.set_ylim (-0.34, 3.4) #This scale is Newtons
      
      self.ax1.yaxis.set_major_locator(plt.MaxNLocator(nbins=5))
      self.twin_ax.set_xlim (-2, self.visible_duration+2)
      self.twin_ax.set_ylim(-30, 300) #This scale is microstrains
      self.twin_ax.set_yticklabels([])

  def plot_drag_live(self, i, data_queue, aoa_meas_queue, liftdrag_est_queue, use_compensated_strains, start_time):
    aoa_meas = np.asarray(aoa_meas_queue)+1.75
    # drag_meas_queue = np.asarray(data_queue)[:,15] #Without correcting for SG rotation.
    princp1_arr = np.asarray(data_queue)[:,14]
    meas_arr = np.asarray(data_queue)[:,15]
    princp2_arr = (0.33*princp1_arr + meas_arr)/0.95
    drag_meas_queue = princp1_arr * np.sin(np.radians(aoa_meas)) + princp2_arr * np.cos(np.radians(aoa_meas))
    drag_est_queue = np.asarray(liftdrag_est_queue)[:,1]
    temp_queue = np.asarray(data_queue)[:,16:18]
    self.meas_line, self.est_line = super().plot_live(i, self.meas_line, self.est_line, drag_meas_queue, drag_est_queue, start_time, 'drag', use_compensated_strains, temp_queue)
    return list((self.meas_line, self.est_line))