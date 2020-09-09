import numpy as np
from scipy import signal
import matplotlib as mpl
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.abspath('./helpers'))
from proc_tempcomp_helper import CommSG_Temp_Comp


class PlotSensorData:
  def __init__(self, visible_duration, downsample_mult, params=None):
    self.params = params
    self.visible_duration = visible_duration
    self.downsample_mult = downsample_mult
    self.fig = plt.figure(figsize=(6.0, 6.0))
    self.ax1 = self.fig.add_subplot(3,1,1)
    self.ax2 = self.fig.add_subplot(3,1,2)
    self.ax3 = self.fig.add_subplot(3,1,3)
    self.init_common_params()


  def init_common_params (self):
    plt.style.use ('fivethirtyeight')
    mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
    mpl.rcParams['axes.edgecolor'] = 'black'
    mpl.rcParams['axes.linewidth'] = 1
    self.fig.tight_layout(pad=2.0)

    self.PZTlines = list()
    self.ax1.set_xlim(0, self.visible_duration)
    self.ax1.set_title("PZT data", fontsize=11)
    self.ax1.set_ylabel("Voltage (V)", labelpad=2, fontsize=11)
    self.ax1.tick_params(labelsize="small")
    self.ax1.grid(False)

    self.SGlines = list()
    self.ax2.set_xlim(0, self.visible_duration)
    self.ax2.set_title("-SSN SGs", fontsize=11)
    self.ax2.set_ylabel("Voltage (V)", labelpad=2, fontsize=11)
    self.ax2.tick_params(labelsize="small")
    self.ax2.grid(False)

    self.ax3.set_xlim(0, self.visible_duration)
    self.ax3.set_title("Commercial SGs", fontsize=11)
    self.ax3.set_xlabel("Time", fontsize=11)
    self.ax3.set_ylabel("Microstrain (us)", labelpad=2, fontsize=11)
    self.ax3.tick_params(labelsize="small")
    self.ax3.grid(False)


  def term_common_params(self):
    self.leg1 = self.ax1.legend(fontsize=7, loc="upper right", ncol=2, columnspacing=1)
    self.leg2 = self.ax2.legend(fontsize=7, loc="upper right", ncol=3, columnspacing=1)
    self.leg3 = self.ax3.legend(fontsize=7, loc="upper right", ncol=2, columnspacing=1)

    for line in self.leg1.get_lines():
      line.set_linewidth(1.5)
    for line in self.leg2.get_lines():
      line.set_linewidth(1.5)
    for line in self.leg3.get_lines():
      line.set_linewidth(1.5)

    plt.tight_layout(pad=1.2)
    plt.show()


  def plot_raw_lines (self, realtime, vel=None, aoa=None, ys=None, plot_refresh_rate=None):
    if realtime:
      self.xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
      self.ys = np.zeros((16,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult)))
      self.num_samples = int(self.params["sample_rate"]*plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.fig.suptitle('Real-time sensor readings', fontsize=12)
      self.ax1.set_ylim(-0.05, 0.05)
      self.ax2.set_ylim(-0.2, 0.2)
      self.ax3.set_ylim(-200, 200)
      self.ax1.set_xticklabels([])
      self.ax2.set_xticklabels([])
      self.ax3.set_xticklabels([])
    else:
      self.xs = np.linspace(0,self.visible_duration,ys.shape[1]) 
      self.ys = ys
      self.fig.suptitle("Readings for V = {}m/s, AoA = {}deg".format(vel,aoa), fontsize=12)
      self.ax1.set_ylim(-0.05, 0.05)
      self.fig.set_size_inches(12.0, 6.0)
      self.ax3.set_xlabel("Time (min)", fontsize=11)


    for i in range(6):
      self.PZTlines.append(self.ax1.plot(self.xs, ys[i], linewidth=0.3, label="PZT {}".format(i+1))[0])
    for i in range(8):
      if i == 7:
        self.SGlines.append(self.ax2.plot(self.xs, ys[6+i], linewidth=0.5, label="SG {}".format(i+2))[0])
      else:
        self.SGlines.append(self.ax2.plot(self.xs, ys[6+i], linewidth=0.5, label="SG {}".format(i+1))[0])
    self.liftline, = self.ax3.plot(self.xs, ys[14], linewidth=0.5, label="Lift")
    self.dragline, = self.ax3.plot(self.xs, ys[15], linewidth=0.5, label="Drag")


  def plot_commSG_tempcomp_lines (self, temp_np_F, poly_coeffs, gage_fact_CTE, SG_matl_CTE, al6061_CTE, gage_fact, k_poly): #NOT IMPLEMENTED FOR REAL-TIME YET.
    temp_np_C = (temp_np_F-32) * 5 / 9
    ref_temp = temp_np_C[0]
    commSG_temp_comp = CommSG_Temp_Comp(poly_coeffs, gage_fact_CTE, SG_matl_CTE, al6061_CTE, ref_temp, gage_fact, k_poly)
    comp_downsampled_commSG, comp_commSG_var = commSG_temp_comp.compensate(self.ys[14:], temp_np_C)
    self.ax3.plot(self.xs, -comp_downsampled_commSG[0], ':', color=self.ax2.lines[0].get_color(), linewidth=0.5, label="SG Lift (compensated)")
    self.ax3.plot(self.xs, -comp_downsampled_commSG[1], ':', color=self.ax2.lines[1].get_color(), linewidth=0.5, label="SG Drag (compensated)")


  #Function to generate real-time plots.
  def plot_live(self, i, ys, queue):
    read_data = queue.get()
    if (i%int(self.visible_duration/self.plot_refresh_rate) == 0): #Refresh data after its filled.
      ys [:,:] = 0
    
    fewerPZTdata = signal.resample(read_data[0:6,:], self.num_samples, axis=1) #Downsample the PZT data
    fewerSGdata = np.mean (read_data[6:,:].reshape(10,-1,self.downsample_mult), axis=2) #Downsample the SG data
    slice_start = i%(int(self.visible_duration/self.plot_refresh_rate))*self.num_samples
    slice_end = i%(int(self.visible_duration/self.plot_refresh_rate))*self.num_samples + self.num_samples
    ys[0:6,slice_start:slice_end] = fewerPZTdata
    ys[6:,slice_start:slice_end] = fewerSGdata
      
    for count,line in enumerate(self.PZTlines):
      line.set_ydata(ys[count])
    for count,line in enumerate(self.SGlines):
      line.set_ydata(ys[count+6])
    self.liftline.set_ydata(ys[14])
    self.dragline.set_ydata(ys[15])
    return self.PZTlines+self.SGlines+list((self.liftline,self.dragline))


  def plot_anemometer_data (self, vel_np, temp_np_F):
    temp_np_C = (temp_np_F-32) * 5 / 9
  
    ax2_veltwin = self.ax2.twinx()
    ax2_temptwin = self.ax2.twinx()
    ax2_temptwin.spines["right"].set_position(("axes", 1.08))
    ax2_veltwin.plot (self.xs, vel_np, "b-", linewidth=0.8,  label="WT Speed")
    ax2_temptwin.plot (self.xs, temp_np_C, "r-", linewidth=0.8,  label="WT Temp")
    ax2_veltwin.set_ylabel("Airspeed (m/s)", fontsize=11)
    ax2_temptwin.set_ylabel("Temperature (C)", fontsize=11)
    ax2_veltwin.yaxis.label.set_color('b')
    ax2_temptwin.yaxis.label.set_color('r')
    ax2_veltwin.tick_params(colors = 'b', labelsize="x-small")
    ax2_temptwin.tick_params(colors = 'r', labelsize="x-small")
    ax2_temptwin.set_ylim((22,26))
    ax2_temptwin.grid(False)
    ax2_veltwin.grid(False)

    ax3_veltwin = self.ax3.twinx()
    ax3_temptwin = self.ax3.twinx()
    ax3_temptwin.spines["right"].set_position(("axes", 1.08))
    ax3_veltwin.plot (self.xs, vel_np, "b-", linewidth=0.8,  label="WT Speed")
    ax3_temptwin.plot (self.xs, temp_np_C, "r-", linewidth=0.8,  label="WT Temp")
    ax3_veltwin.set_ylabel("Airspeed (m/s)", fontsize=11)
    ax3_temptwin.set_ylabel("Temperature (C)", fontsize=11)
    ax3_veltwin.yaxis.label.set_color('b')
    ax3_temptwin.yaxis.label.set_color('r')
    ax3_veltwin.tick_params(colors = 'b', labelsize="x-small")
    ax3_temptwin.tick_params(colors = 'r', labelsize="x-small")
    ax3_temptwin.set_ylim((22,26))
    ax3_temptwin.grid(False)
    ax3_veltwin.grid(False)