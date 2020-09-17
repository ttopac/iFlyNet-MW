import numpy as np
from scipy import signal
import matplotlib as mpl
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.abspath('./helpers'))
import proc_tempcomp_helper

#Comm. SG compensation parameters
poly_coeffs = (-23.65, 2.06, -5.02E-2, 2.26E-4, 0.3, 0.219)
gage_fact, k_poly = 2, 2
gage_fact_CTE, SG_matl_CTE = 93E-6, 10.8E-6
al6061_CTE = 23.6E-6

#SSN SG compensation parameters (skipping SG8)
r_total = np.asarray ([14, 14.4, 14.1, 15.3, 14.7, 14, 14.3, 13.9])
r_wire = np.asarray ([0.65, 0.6, 0.65, 1.3, 0, 0.2, 0.5, 0.2]) #Values from Sept16. From Xiyuan: [0.4, 0.6, 0.3, 1.5, 0.9, 0.2, 0.5, 0.1]
alpha_gold = 1857.5
alpha_constantan = 21.758

class PlotSensorData:
  def __init__(self, visible_duration, downsample_mult, params=None):
    self.params = params
    self.visible_duration = visible_duration
    self.downsample_mult = downsample_mult
    self.fig = plt.figure(figsize=(6.0, 3.0))
    self.ax1 = self.fig.add_subplot(3,1,1)
    self.ax2 = self.fig.add_subplot(3,1,2)
    self.ax3 = self.fig.add_subplot(3,1,3)
    self.init_common_params()


  def init_common_params (self):
    plt.style.use ('fivethirtyeight')
    mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
    mpl.rcParams['axes.edgecolor'] = 'black'
    mpl.rcParams['axes.linewidth'] = 1

    self.PZTlines = list()
    self.ax1.set_xlim(0, self.visible_duration)
    self.ax1.set_title("PZT data", fontsize=11)
    self.ax1.set_ylabel("Voltage (V)", labelpad=2, fontsize=11)
    self.ax1.tick_params(labelsize="small")
    self.ax1.grid(False)

    self.SGlines = list()
    self.ax2.set_xlim(0, self.visible_duration)
    self.ax2.set_title("-SSN SGs", fontsize=11)
    self.ax2.set_ylabel("Microstrain (ue)", labelpad=2, fontsize=11)
    self.ax2.tick_params(labelsize="small")
    self.ax2.grid(False)

    self.ax3.set_xlim(0, self.visible_duration)
    self.ax3.set_title("-Commercial SGs", fontsize=11)
    self.ax3.set_xlabel("Time", fontsize=11)
    self.ax3.set_ylabel("Microstrain (ue)", labelpad=2, fontsize=11)
    self.ax3.tick_params(labelsize="small")
    self.ax3.grid(False)

  def term_common_params(self, realtime):
    self.leg1 = self.ax1.legend(fontsize=7, loc="upper right", ncol=2, columnspacing=1)
    self.leg2 = self.ax2.legend(fontsize=7, loc="upper right", ncol=3, columnspacing=1)
    self.leg3 = self.ax3.legend(fontsize=7, loc="upper right", ncol=2, columnspacing=1)

    for line in self.leg1.get_lines():
      line.set_linewidth(1.5)
    for line in self.leg2.get_lines():
      line.set_linewidth(1.5)
    for line in self.leg3.get_lines():
      line.set_linewidth(1.5)
    
    if realtime:
      plt.tight_layout(pad=1.5)
    else:
      self.fig.set_size_inches(12.0, 6.0)
      plt.tight_layout(pad=1.3)

  def plot_raw_lines (self, realtime, vel=None, aoa=None, ys=None, plot_refresh_rate=None):
    if realtime:
      self.xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
      self.ys = np.zeros((16,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult)))
      self.num_samples = int(self.params["sample_rate"]*plot_refresh_rate/self.downsample_mult) #number of samples coming at each call to plot_live function
      self.ax1.set_ylim(-0.05, 0.05)
      self.ax2.set_ylim(50, 50)
      self.ax3.set_ylim(-200, 200)
      self.ax1.set_xticklabels([])
      self.ax2.set_xticklabels([])
      self.ax3.set_xticklabels([])
    else:
      self.xs = np.linspace(0,self.visible_duration,ys.shape[1]) 
      self.ys = ys
      self.fig.suptitle("Readings for V = {}m/s, AoA = {}deg".format(vel,aoa), fontsize=12)
      self.ax1.set_ylim(-0.05, 0.05)
      self.ax3.set_xlabel("Time (min)", fontsize=11)

    for i in range(6): #PZTs
      self.PZTlines.append(self.ax1.plot(self.xs, self.ys[i], linewidth=0.3, label="PZT {}".format(i+1))[0])
    for i in range(8): #SSNSGs
      if i == 7:
        self.SGlines.append(self.ax2.plot(self.xs, -self.ys[6+i], linewidth=0.5, label="SG {}".format(i+2))[0])
      else:
        self.SGlines.append(self.ax2.plot(self.xs, -self.ys[6+i], linewidth=0.5, label="SG {}".format(i+1))[0])
    self.liftline, = self.ax3.plot(self.xs, -self.ys[14], linewidth=0.5, label="Lift") #Comm. LiftSG
    self.dragline, = self.ax3.plot(self.xs, -self.ys[15], linewidth=0.5, label="Drag") #Comm. DragSG


  #Function to generate real-time plots.
  def plot_live(self, i, ys, queue, plot_refresh_rate, plot_compensated_strains=True, only_plot=True):
    if only_plot:
      read_data = queue.get()
    else:
      read_data = queue.get()
      queue.put_nowait(read_data)
    if i == 0: #Set initial temperature at the beginning
      ref_temp = np.mean(read_data[16])
    if (i%int(self.visible_duration/plot_refresh_rate) == 0): #Reset data once the period is filled.
      ys [:,:] = 0
    
    fewerPZTdata = signal.resample(read_data[0:6,:], self.num_samples, axis=1) #Downsample the PZT data
    fewerSSNSGdata = np.mean (read_data[6:14,:].reshape(8,-1,self.downsample_mult), axis=2) #Downsample the SSNSG data
    fewerCommSGdata = np.mean (read_data[14:16,:].reshape(2,-1,self.downsample_mult), axis=2) #Downsample the CommSG data
    temp_np_C = np.mean(read_data[16])
    SSNSG_temp_comp = proc_tempcomp_helper.SSNSG_Temp_Comp(ref_temp, r_total, r_wire, alpha_gold, alpha_constantan)
    compSSNSGdata = SSNSG_temp_comp.compensate(self.ys[6:14], temp_np_C)
    commSG_temp_comp = proc_tempcomp_helper.CommSG_Temp_Comp(poly_coeffs, gage_fact_CTE, SG_matl_CTE, al6061_CTE, ref_temp, gage_fact, k_poly)
    compCommSGdata, compCommSGdata_var = commSG_temp_comp.compensate(self.ys[14:16], temp_np_C)

    slice_start = i%(int(self.visible_duration/plot_refresh_rate))*self.num_samples
    slice_end = i%(int(self.visible_duration/plot_refresh_rate))*self.num_samples + self.num_samples
    ys[0:6,slice_start:slice_end] = fewerPZTdata
    if plot_compensated_strains:
      ys[6:14,slice_start:slice_end] = compSSNSGdata
      ys[14:16,slice_start:slice_end] = compCommSGdata
    else:  
      ys[6:14,slice_start:slice_end] = fewerSSNSGdata
      ys[14:16,slice_start:slice_end] = fewerCommSGdata
      
    for count,line in enumerate(self.PZTlines):
      line.set_ydata(ys[count])
    for count,line in enumerate(self.SGlines):
      line.set_ydata(-ys[count+6])
    self.liftline.set_ydata(-ys[14])
    self.dragline.set_ydata(-ys[15])
    return self.PZTlines+self.SGlines+list((self.liftline,self.dragline))

  #Temperature-related functions
  def plot_commSG_tempcomp_lines (self, temp_np_C, poly_coeffs, gage_fact_CTE, SG_matl_CTE, al6061_CTE, gage_fact, k_poly, ref_temp=None): #NOT IMPLEMENTED FOR REAL-TIME YET.
    ref_temp = temp_np_C[0]
    commSG_temp_comp = proc_tempcomp_helper.CommSG_Temp_Comp(poly_coeffs, gage_fact_CTE, SG_matl_CTE, al6061_CTE, ref_temp, gage_fact, k_poly)
    comp_downsampled_commSG, comp_commSG_var = commSG_temp_comp.compensate(self.ys[14:16], temp_np_C)
    self.ax3.plot(self.xs, -comp_downsampled_commSG[0], ':', color=self.ax3.lines[0].get_color(), linewidth=0.5, label="SG Lift (compensated)")
    self.ax3.plot(self.xs, -comp_downsampled_commSG[1], ':', color=self.ax3.lines[1].get_color(), linewidth=0.5, label="SG Drag (compensated)")

  def plot_SSNSG_tempcomp_lines (self, temp_np_C, r_total, r_wire, alpha_gold, alpha_constantan, ref_temp=None):
    ref_temp = temp_np_C[0]
    SSNSG_temp_comp = proc_tempcomp_helper.SSNSG_Temp_Comp(ref_temp, r_total, r_wire, alpha_gold, alpha_constantan)
    comp_downsampled_SSNSG = SSNSG_temp_comp.compensate(self.ys[6:14], temp_np_C)
    self.compSGlines = list()
    for i in range(8):
      if i == 7:
        self.compSGlines.append(self.ax2.plot(self.xs, -comp_downsampled_SSNSG[i], ':', color=self.SGlines[i].get_color(), linewidth=0.5, label="SG {} (comp)".format(i+2))[0])
      else:
        self.compSGlines.append(self.ax2.plot(self.xs, -comp_downsampled_SSNSG[i], ':', color=self.SGlines[i].get_color(), linewidth=0.5, label="SG {} (comp)".format(i+1))[0])

  def plot_anemometer_data (self, vel_np, temp_np_C):  
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
    ax2_temptwin.set_ylim((18,26))
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
    ax3_temptwin.set_ylim((18,26))
    ax3_temptwin.grid(False)
    ax3_veltwin.grid(False)

  def plot_RTD_data (self, temp_np_C):  
    ax2_temptwin = self.ax2.twinx()
    ax2_temptwin.spines["right"].set_position(("axes", 1.02))
    ax2_temptwin.plot (self.xs, temp_np_C, "r-", linewidth=0.8,  label="Wing Temp")
    ax2_temptwin.set_ylabel("Temperature (C)", fontsize=11)
    ax2_temptwin.yaxis.label.set_color('r')
    ax2_temptwin.tick_params(colors = 'r', labelsize="x-small")
    ax2_temptwin.grid(False)

    ax3_temptwin = self.ax3.twinx()
    ax3_temptwin.spines["right"].set_position(("axes", 1.02))
    ax3_temptwin.plot (self.xs, temp_np_C, "r-", linewidth=0.8,  label="Wing Temp")
    ax3_temptwin.set_ylabel("Temperature (C)", fontsize=11)
    ax3_temptwin.yaxis.label.set_color('r')
    ax3_temptwin.tick_params(colors = 'r', labelsize="x-small")
    ax3_temptwin.grid(False)
