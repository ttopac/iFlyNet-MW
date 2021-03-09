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

  def init_common_params (self, y_label):
    mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
    mpl.rcParams['axes.edgecolor'] = 'black'
    mpl.rcParams['axes.linewidth'] = 1
    
    self.fig = plt.figure()
    self.ax1 = self.fig.add_subplot(1,1,1)
    self.ax1.set_xlabel("Time", labelpad=2, fontsize=11)
    self.ax1.set_ylabel(y_label, labelpad=2, fontsize=11) #Commented out for simplification. We are showing trends, not absolute values.
    self.ax1.grid(False)

  def term_common_params (self):
    self.leg1 = self.ax1.legend(fontsize=9, loc="upper right", ncol=1, columnspacing=1)
    
    for line in self.leg1.get_lines():
      line.set_linewidth(1.5)
      line.set_markersize(1.5)
    
    if self.ongui:
      self.fig.set_size_inches(3.5, 3.0) #width, height
      plt.tight_layout()


class AirspeedPlot (PlotsWComparison):
  def __init__(self, pred_sample_size, ongui, offline):
    super().__init__(pred_sample_size, ongui, offline)
  def init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate):
    super().init_realtime_params(visible_duration, downsample_mult, params, plot_refresh_rate) 
  def init_common_params(self, y_label):
    super().init_common_params(y_label)
  def term_common_params(self):
    super().term_common_params()

  def plot_airspeed_wcomparison(self, xs, ys):
    if self.ongui:
      self.xs = xs
      self.ys = ys
      self.num_samples = int(self.params["sample_rate"]*self.plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_ylim(-2, 22)
      self.ax1.set_xticklabels([])
      self.meas_line, = self.ax1.plot(self.xs, self.ys[0], linewidth=0.5, label="Measured") 
      self.est_line, = self.ax1.plot(self.xs, self.ys[1], linewidth=0.5, label="Predicted")

  def plot_airspeed_live(self, i, vel_meas_queue, est_queue, start_time):
    vel_meas_queue = np.asarray(vel_meas_queue)
    vel_est_queue = np.asarray(est_queue)[:,0]
    
    t0 = time.time()
    cur_frame = int((t0-start_time)/self.plot_refresh_rate)
    
    meas_data = vel_meas_queue[cur_frame]
    est_data = vel_est_queue[cur_frame]
    
    if (i%int(self.visible_duration/self.plot_refresh_rate) == 0): #Reset data once the period is filled.
      self.ys [:,:] = 0

    slice_start = i%(int(self.visible_duration/self.plot_refresh_rate))
    slice_end = i%(int(self.visible_duration/self.plot_refresh_rate)) + int(1/self.plot_refresh_rate)
    
    self.ys[0,slice_start:slice_end] = meas_data
    self.ys[1,slice_start:slice_end] = est_data
    self.meas_line.set_ydata(self.ys[0])
    self.est_line.set_ydata(self.ys[1])

    return list((self.meas_line, self.est_line))
    

class AoaPlot (PlotsWComparison):
  def __init__(self, pred_sample_size, ongui, offline):
    super().__init__(pred_sample_size, ongui, offline)
  def init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate):
    super().init_realtime_params(visible_duration, downsample_mult, params, plot_refresh_rate) 
  def init_common_params(self, y_label):
    super().init_common_params(y_label)
  def term_common_params(self):
    super().term_common_params()

  def plot_aoa_wcomparison(self, xs, ys):
    if self.ongui:
      self.xs = xs
      self.ys = ys
      self.num_samples = int(self.params["sample_rate"]*self.plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_ylim(-2, 22)
      self.ax1.set_xticklabels([])
      self.meas_line, = self.ax1.plot(self.xs, self.ys[0], linewidth=0.5, label="Measured") 
      self.est_line, = self.ax1.plot(self.xs, self.ys[1], linewidth=0.5, label="Predicted")

  def plot_aoa_live(self, i, aoa_meas_queue, est_queue, start_time):
    aoa_meas_queue = np.asarray(aoa_meas_queue)
    aoa_est_queue = np.asarray(est_queue)[:,1]
    
    t0 = time.time()
    cur_frame = int((t0-start_time)/self.plot_refresh_rate)
    
    meas_data = aoa_meas_queue[cur_frame]
    est_data = aoa_est_queue[cur_frame]
    
    if (i%int(self.visible_duration/self.plot_refresh_rate) == 0): #Reset data once the period is filled.
      self.ys [:,:] = 0

    slice_start = i%(int(self.visible_duration/self.plot_refresh_rate))
    slice_end = i%(int(self.visible_duration/self.plot_refresh_rate)) + int(1/self.plot_refresh_rate)
    
    self.ys[0,slice_start:slice_end] = meas_data
    self.ys[1,slice_start:slice_end] = est_data
    self.meas_line.set_ydata(self.ys[0])
    self.est_line.set_ydata(self.ys[1])

    return list((self.meas_line, self.est_line))


class LiftPlot (PlotsWComparison):
  def __init__(self, pred_sample_size, ongui, offline):
    super().__init__(pred_sample_size, ongui, offline)
  def init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate):
    super().init_realtime_params(visible_duration, downsample_mult, params, plot_refresh_rate) 
  def init_common_params(self, y_label):
    super().init_common_params(y_label)
  def term_common_params(self):
    super().term_common_params()

  def plot_lift_wcomparison(self, xs, ys):
    if self.ongui:
      self.xs = xs
      self.ys = ys
      self.num_samples = int(self.params["sample_rate"]*self.plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_ylim(-25, 275) #TODO: Change based on obtained values
      self.ax1.set_xticklabels([])
      self.ax1.set_yticklabels([])
      self.meas_line, = self.ax1.plot(self.xs, -self.ys[0], linewidth=0.5, label="Measured") 
      self.est_line, = self.ax1.plot(self.xs, self.ys[1], linewidth=0.5, label="Predicted")
  
  def plot_lift_live(self, i, data_queue, liftdrag_est_queue, use_compensated_strains, start_time):
    lift_meas_queue = np.asarray(data_queue)[:,14]
    lift_est_queue = np.asarray(liftdrag_est_queue)[:,0]
    temp_queue = np.asarray(data_queue)[:,16:18]
    
    #Here meas_queue and est_queue contains lists of shape (plot_time/plot_refresh_rate,). This is (3000,) for 300 seconds of data at 10 hz.
    t0 = time.time()
    cur_frame = int((t0-start_time)/self.plot_refresh_rate)
    
    meas_data = lift_meas_queue[cur_frame]
    est_data = lift_est_queue[cur_frame]
    temp_data = temp_queue[cur_frame]
    
    if i == 0: #Set initial temperature at the beginning
      self.ref_temp_SG1 = temp_data[0]
      self.ref_temp_wing = temp_data[1]
    if (i%int(self.visible_duration/self.plot_refresh_rate) == 0): #Reset data once the period is filled.
      self.ys [:,:] = 0

    if use_compensated_strains:
      meas_temp_comp = proc_tempcomp_helper.CommSG_Temp_Comp(self.ref_temp_SG1, self.ref_temp_wing)
      meas_data, _ = meas_temp_comp.compensate(meas_data, temp_data[1], 'rod', 0)

    slice_start = i%(int(self.visible_duration/self.plot_refresh_rate))
    slice_end = i%(int(self.visible_duration/self.plot_refresh_rate)) + int(1/self.plot_refresh_rate)
    
    self.ys[0,slice_start:slice_end] = meas_data
    self.ys[1,slice_start:slice_end] = est_data
    self.meas_line.set_ydata(-self.ys[0])
    self.est_line.set_ydata(self.ys[1])

    return list((self.meas_line, self.est_line))


class DragPlot (PlotsWComparison):
  def __init__(self, pred_sample_size, ongui, offline):
    super().__init__(pred_sample_size, ongui, offline)
  def init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate):
    super().init_realtime_params(visible_duration, downsample_mult, params, plot_refresh_rate) 
  def init_common_params(self, y_label):
    super().init_common_params(y_label)
  def term_common_params(self):
    super().term_common_params()

  def plot_drag_wcomparison(self, xs, ys):
    if self.ongui:
      self.xs = xs
      self.ys = ys
      self.num_samples = int(self.params["sample_rate"]*self.plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_ylim(-25, 275) #TODO: Change based on obtained values
      self.ax1.set_xticklabels([])
      self.ax1.set_yticklabels([])
      self.meas_line, = self.ax1.plot(self.xs, -self.ys[0], linewidth=0.5, label="Measured") 
      self.est_line, = self.ax1.plot(self.xs, self.ys[1], linewidth=0.5, label="Predicted")

  def plot_drag_live(self, i, data_queue, liftdrag_est_queue, use_compensated_strains, start_time):
    drag_meas_queue = np.asarray(data_queue)[:,15]
    drag_est_queue = np.asarray(liftdrag_est_queue)[:,1]
    temp_queue = np.asarray(data_queue)[:,16:18]
    
    #Here meas_queue and est_queue contains lists of shape (plot_time/plot_refresh_rate,). This is (3000,) for 300 seconds of data at 10 hz.
    t0 = time.time()
    cur_frame = int((t0-start_time)/self.plot_refresh_rate)
    
    meas_data = drag_meas_queue[cur_frame]
    est_data = drag_est_queue[cur_frame]
    temp_data = temp_queue[cur_frame]
    
    if i == 0: #Set initial temperature at the beginning
      self.ref_temp_SG1 = temp_data[0]
      self.ref_temp_wing = temp_data[1]
    if (i%int(self.visible_duration/self.plot_refresh_rate) == 0): #Reset data once the period is filled.
      self.ys [:,:] = 0

    if use_compensated_strains:
      meas_temp_comp = proc_tempcomp_helper.CommSG_Temp_Comp(self.ref_temp_SG1, self.ref_temp_wing)
      meas_data, _ = meas_temp_comp.compensate(meas_data, temp_data[1], 'rod', 0)

    slice_start = i%(int(self.visible_duration/self.plot_refresh_rate))
    slice_end = i%(int(self.visible_duration/self.plot_refresh_rate)) + int(1/self.plot_refresh_rate)
    
    self.ys[0,slice_start:slice_end] = meas_data
    self.ys[1,slice_start:slice_end] = est_data
    self.meas_line.set_ydata(-self.ys[0])
    self.est_line.set_ydata(self.ys[1])

    return list((self.meas_line, self.est_line))