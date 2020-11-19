import time
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import sys, os
sys.path.append(os.path.abspath('./helpers'))
import proc_keras_estimates_helper
import proc_tempcomp_helper

class PlotData:
  def __init__(self, pred_freq, estimates=None, singleplot=False, ongui=False, offline=False):
    self.pred_freq = pred_freq
    self.singleplot = singleplot #Whether lift and drag lines are on the same plot.
    self.ongui = ongui #Whether the plot will be placed on a TK GUI.
    self.fig = plt.figure()
    self.estimates = estimates #--OLD line only for overlaid stall. Updated with models implementation. proc_keras_estimates_helper.iFlyNetEstimates(pred_freq, stall_model_path, liftdrag_model_path) #Initialize Keras estimates if this is not running in realtime
    self.offline = offline

    self.init_common_params()

  def init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate):
    self.visible_duration = visible_duration
    self.downsample_mult = downsample_mult
    self.params = params
    self.plot_refresh_rate = plot_refresh_rate

  def init_common_params (self):
    # plt.style.use ('fivethirtyeight')
    mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
    mpl.rcParams['axes.edgecolor'] = 'black'
    mpl.rcParams['axes.linewidth'] = 1

    if not self.singleplot:
      self.ax1 = self.fig.add_subplot(2,1,1) #Lift
      self.ax2 = self.fig.add_subplot(2,1,2) #Drag
      self.ax1.set_title("Lift", fontsize=11)
      self.ax1.set_xlabel("Time (sec)", labelpad=2, fontsize=11)
      self.ax1.set_ylabel("Microstrain (ue)", labelpad=2, fontsize=11)
      self.ax1.tick_params(labelsize="small")
      self.ax1.grid(False)
      self.ax2.set_title("Drag", fontsize=11)
      self.ax2.set_xlabel("Time (sec)", labelpad=2, fontsize=11)
      self.ax2.set_ylabel("Microstrain (ue)", labelpad=2, fontsize=11)
      self.ax2.tick_params(labelsize="small")
      self.ax2.grid(False)
    else:
      self.ax1 = self.fig.add_subplot(1,1,1) #Both lift and drag
      self.ax1.set_xlabel("Time", labelpad=2, fontsize=11)
      self.ax1.set_ylabel("Microstrain (ue)", labelpad=2, fontsize=11)
      self.ax1.tick_params(labelsize="small")
      self.ax1.grid(False)

  def term_common_params(self, stall_overlay=False):
    if stall_overlay: # Legend for lift is a little more complicated if there's stall too
      lns = self.ln1+self.ln2+self.ln3
      labs = [l.get_label() for l in lns]
      self.leg1 = self.ax1.legend(lns, labs, fontsize=7, loc="upper right", ncol=1, columnspacing=1)
    else:
      self.leg1 = self.ax1.legend(fontsize=7, loc="upper right", ncol=1, columnspacing=1)
    
    for line in self.leg1.get_lines():
      line.set_linewidth(1.5)
      line.set_markersize(1.5)

    if not self.singleplot: #There's also drag plot in seperate axis
      self.leg2 = self.ax2.legend(fontsize=7, loc="upper right", ncol=1, columnspacing=1)
      for line in self.leg2.get_lines():
        line.set_linewidth(1.5)
    
    if self.ongui:
      self.fig.set_size_inches(4.0, 3.0) #width, height
    else:
      self.fig.set_size_inches(6.0, 6.0)
      plt.tight_layout(pad=1.3)
      plt.show()

  def plot_liftdrag (self, xs, ys): #Tempcomp is not implemented yet.
    if not self.ongui:
      if not self.singleplot:
        self.ln1 = self.ax1.plot(xs, -ys[14], linewidth=1.0, label="SG Lift")
        self.ax2.plot(xs, -ys[15], color='#ff7f0e', linewidth=1.0, label="SG Drag")
    else: #Realtime is only for singleplot
      self.xs = xs
      self.ys = ys
      self.num_samples = int(self.params["sample_rate"]*self.plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_ylim(-25, 275)
      self.ax1.set_xticklabels([])
      self.liftline, = self.ax1.plot(self.xs, -self.ys[0], linewidth=0.5, label="Lift") #Comm. LiftSG
      self.dragline, = self.ax1.plot(self.xs, -self.ys[1], linewidth=0.5, label="Drag") #Comm. DragSG

  def plot_stall_est (self, ys): #Overlaid stall plot is for non-realtime only
    preds = self.estimates.estimate_stall(ys, False)
    ax1_stalltwin = self.ax1.twinx()
    ax1_stalltwin.spines["right"].set_position(("axes", 1.02))
    ax1_stalltwin.spines["right"].set_edgecolor('r')
    self.ln3 = ax1_stalltwin.plot (self.xs, preds, "*", markersize=3, color='r', label="Stall?")
    ax1_stalltwin.set_ylabel("Stall?", fontsize=11)
    ax1_stalltwin.yaxis.label.set_color('r')
    loc = plticker.MultipleLocator(base=1.0) #Define ticker to put ticks only at 0 and 1
    ax1_stalltwin.yaxis.set_major_locator(loc)
    ax1_stalltwin.tick_params(colors = 'r', labelsize="x-small")
    ax1_stalltwin.grid(False)

  def plot_live(self, i, ys, queue, plot_compensated_strains=True, estimate_data=False, start_time=None):
    sensor_start_index = 0 if estimate_data else 14
    if estimate_data:
      plot_compensated_strains = False
    if not self.offline:
      read_data = queue.get()
      queue.put_nowait(read_data)
    else:
      t0 = time.time()
      cur_frame = int((t0-start_time)/self.plot_refresh_rate)
      read_data = queue[cur_frame]

    if i == 0 and not estimate_data: #Set initial temperature at the beginning
      ref_temp = np.mean(read_data[16])
    if (i%int(self.visible_duration/self.plot_refresh_rate) == 0): #Reset data once the period is filled.
      ys [:,:] = 0
    
    if not estimate_data:
      temp_np_C = np.mean(read_data[sensor_start_index+2])
      useful_data_start, useful_data_end = 0, int(read_data.shape[1]/self.downsample_mult)*self.downsample_mult
      fewerCommSGdata = np.mean (read_data[sensor_start_index:sensor_start_index+2,useful_data_start:useful_data_end].reshape(2,-1,self.downsample_mult), axis=2) #Downsample the CommSG data
    else:
      fewerCommSGdata = read_data.T

    slice_start = i%(int(self.visible_duration/self.plot_refresh_rate))*self.num_samples
    slice_end = i%(int(self.visible_duration/self.plot_refresh_rate))*self.num_samples + self.num_samples
    if plot_compensated_strains:
      commSG_temp_comp = proc_tempcomp_helper.CommSG_Temp_Comp(ref_temp)
      fewerCommSGdata, compCommSGdata_var = commSG_temp_comp.compensate(fewerCommSGdata, temp_np_C)
    if slice_end > ys.shape[1]:
      ys[:,slice_start:slice_end] = fewerCommSGdata[:,0] #(sensor(lift/drag), time)
    else:
      ys[:,slice_start:slice_end] = fewerCommSGdata
    
    self.liftline.set_ydata(-ys[0])
    self.dragline.set_ydata(-ys[1])

    return list((self.liftline,self.dragline))