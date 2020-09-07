# This script can be used to plot several sensor signals in real-time.
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
from nidaqmx import stream_readers
from nidaqmx import Task

import numpy as np
from scipy import signal
import time
import math

import tkinter as tk
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from multiprocessing import Process, Queue, Pipe
from concurrent.futures import ThreadPoolExecutor
import sys
import os
sys.path.append(os.path.abspath('./fbf-DAQ'))
from capture_SG_offsets import send_SG_offsets
from capture_data import send_data

#Initialize the DAQ and SG parameters
params = dict()
SGcoeffs = dict()
params["sample_rate"] = 1000
downsample_mult = 1
SGcoeffs["amplifier_coeff"] = 100
SGcoeffs["GF"] = 2.11
SGcoeffs["Vex"] = 12

#Plotting coefficients
plot_refresh_rate = 1 #seconds
visible_duration = 30 #seconds
num_samples = int(params["sample_rate"]*plot_refresh_rate/downsample_mult)

#Initialize the GUI
root = tk.Tk()
root.title ("Real-time Plotting")

#Initialize the plot:
plt.style.use ('fivethirtyeight')
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
mpl.rcParams['axes.edgecolor'] = 'black'
mpl.rcParams['axes.linewidth'] = 1

fig = plt.figure(figsize=(6.0, 6.0))
ax1 = fig.add_subplot(3,1,1)
ax2 = fig.add_subplot(3,1,2)
ax3 = fig.add_subplot(3,1,3)
fig.tight_layout(pad=2.0)
xs = np.linspace (0, visible_duration, int(visible_duration*params["sample_rate"]/downsample_mult))
ys = np.zeros((16,int(visible_duration*params["sample_rate"]/downsample_mult)))
yinterp = np.zeros((16,int(visible_duration*params["sample_rate"]/downsample_mult)))

PZTlines = list()
for i in range(6):
  PZTlines.append(ax1.plot(xs, ys[i], linewidth=0.3, label="PZT {}".format(i+1))[0])
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

SGlines = list()
for i in range(2,6):
  if i == 7:
    SGlines.append(ax2.plot(xs, ys[6+i], linewidth=0.5, label="SG {}".format(i+2))[0])
  else:
    SGlines.append(ax2.plot(xs, ys[6+i], linewidth=0.5, label="SG {}".format(i+1))[0])
ax2.set_xlim(0, visible_duration)
ax2.set_ylim(-0.005, 0.005)
leg2 = ax2.legend(fontsize=7, loc="upper right", ncol=3, columnspacing=1)
for line in leg2.get_lines():
  line.set_linewidth(1.5)
ax2.set_title("SG Data", fontsize=12)
ax2.set_xlabel("Time", fontsize=11)
ax2.set_ylabel("Voltage (V)", labelpad=-2, fontsize=11)
ax2.set_xticklabels([])
ax2.tick_params(labelsize="small")

liftline, = ax3.plot(xs, ys[14], linewidth=0.5, label="Lift")
dragline, = ax3.plot(xs, ys[15], linewidth=0.5, label="Drag")
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
def plot_live(i, ys, yinterp):
  global read_data
  if (i%int(visible_duration/plot_refresh_rate) == 0):
    ys [:,:] = 0
    yinterp [:,:] = 0
  
  fewerPZTdata = signal.resample(read_data[0:6,:], num_samples, axis=1) #Downsample the PZT data
  fewerSGdata = np.mean (read_data[6:,:].reshape(10,-1,downsample_mult), axis=2) #Downsample the SG data
  prev_slice_start = i%(int(visible_duration/plot_refresh_rate))*num_samples - num_samples
  prev_slice_end = i%(int(visible_duration/plot_refresh_rate))*num_samples
  slice_start = i%(int(visible_duration/plot_refresh_rate))*num_samples
  slice_end = i%(int(visible_duration/plot_refresh_rate))*num_samples + num_samples
  ys[0:6,slice_start:slice_end] = fewerPZTdata
  ys[6:,slice_start:slice_end] = fewerSGdata
  yinterp [6:,slice_start:slice_end] = fewerSGdata

  # if (i>1) and np.any(np.abs(fewerSGdata[:-2,0:]) > 5000*np.abs(yinterp[6:-2,prev_slice_start:prev_slice_end])): #Reject drastic jumps.
  #   ys[6:,slice_start:slice_end] = ys[6:,prev_slice_start:prev_slice_end]
  #   print (fewerSGdata[0,50])
    
  for count,line in enumerate(PZTlines):
    line.set_ydata(ys[count])
  for count,line in enumerate(SGlines):
    line.set_ydata(ys[count+6])
  liftline.set_ydata(ys[14])
  dragline.set_ydata(ys[15])
  return PZTlines+SGlines+list((liftline,dragline))

if __name__ == "__main__":
  global read_data

  # Get strain gauge offsets for calibration
  parent_conn, child_conn = Pipe()
  p = Process(target = send_SG_offsets, args=(params["sample_rate"], params["sample_rate"], child_conn))
  p.start()
  SGoffsets = parent_conn.recv()
  p.join()

  # Run capture data in background
  executor = ThreadPoolExecutor(max_workers=2)
  executor.submit(send_data, SGoffsets, params["sample_rate"], int(params["sample_rate"]*plot_refresh_rate), "continuous")
  time.sleep(0.5)
  from capture_data import read_data

  # Plot the data
  canvas = FigureCanvasTkAgg(fig, master=root)
  canvas.get_tk_widget().grid(column=0, row=1)
  ani = FuncAnimation(fig, plot_live, fargs=(ys,yinterp), interval=plot_refresh_rate*1000, blit=True, cache_frame_data=True)
  root.mainloop()
