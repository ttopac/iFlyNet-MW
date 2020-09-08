import numpy as np
from scipy import signal

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PlotRealtime:
  def __init__(self, params, visible_duration, plot_refresh_rate, downsample_mult):
    self.visible_duration = visible_duration
    self.plot_refresh_rate = plot_refresh_rate
    self.downsample_mult = downsample_mult
    self.num_samples = int(params["sample_rate"]*plot_refresh_rate/downsample_mult)
    self.fig = plt.figure(figsize=(6.0, 6.0))
    
    plt.style.use ('fivethirtyeight')
    mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
    mpl.rcParams['axes.edgecolor'] = 'black'
    mpl.rcParams['axes.linewidth'] = 1

    ax1 = self.fig.add_subplot(3,1,1)
    ax2 = self.fig.add_subplot(3,1,2)
    ax3 = self.fig.add_subplot(3,1,3)
    self.fig.tight_layout(pad=2.0)
    xs = np.linspace (0, visible_duration, int(visible_duration*params["sample_rate"]/downsample_mult))
    ys = np.zeros((16,int(visible_duration*params["sample_rate"]/downsample_mult)))

    self.PZTlines = list()
    for i in range(6):
      self.PZTlines.append(ax1.plot(xs, ys[i], linewidth=0.3, label="PZT {}".format(i+1))[0])
    ax1.set_xlim(0, visible_duration)
    ax1.set_ylim(-0.05, 0.05)
    leg1 = ax1.legend(fontsize=7, loc="upper right", ncol=2, columnspacing=1)
    for line in leg1.get_lines():
      line.set_linewidth(1.5)
    ax1.set_title("PZT data", fontsize=12)
    ax1.set_xlabel("Time", fontsize=11)
    ax1.set_ylabel("Voltage (V)", labelpad=1, fontsize=11)
    ax1.set_xticklabels([])
    ax1.tick_params(labelsize="small")

    self.SGlines = list()
    for i in range(8):
      if i == 7:
        self.SGlines.append(ax2.plot(xs, ys[6+i], linewidth=0.5, label="SG {}".format(i+2))[0])
      else:
        self.SGlines.append(ax2.plot(xs, ys[6+i], linewidth=0.5, label="SG {}".format(i+1))[0])
    ax2.set_xlim(0, visible_duration)
    ax2.set_ylim(-0.2, 0.2)
    leg2 = ax2.legend(fontsize=7, loc="upper right", ncol=3, columnspacing=1)
    for line in leg2.get_lines():
      line.set_linewidth(1.5)
    ax2.set_title("SG Data", fontsize=12)
    ax2.set_xlabel("Time", fontsize=11)
    ax2.set_ylabel("Voltage (V)", labelpad=-2, fontsize=11)
    ax2.set_xticklabels([])
    ax2.tick_params(labelsize="small")

    self.liftline, = ax3.plot(xs, ys[14], linewidth=0.5, label="Lift")
    self.dragline, = ax3.plot(xs, ys[15], linewidth=0.5, label="Drag")
    ax3.set_xlim(0, visible_duration)
    ax3.set_ylim(-200, 200)
    leg3 = ax3.legend(fontsize=7, loc="upper right", ncol=3, columnspacing=1)
    for line in leg3.get_lines():
      line.set_linewidth(1.5)
    ax3.set_title("Commercial SGs", fontsize=12)
    ax3.set_xlabel("Time", fontsize=11)
    ax3.set_ylabel("Strain", labelpad=-2, fontsize=11)
    ax3.set_xticklabels([])
    ax3.tick_params(labelsize="small")

  #Function to generate real-time plots.
  def plot_live(self, i, ys, queue):
    read_data = queue.get()
    # print ("Data read by plotting function: ", end="")
    # print (np.mean(read_data[13]))
    # print ()
    if (i%int(self.visible_duration/self.plot_refresh_rate) == 0):
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