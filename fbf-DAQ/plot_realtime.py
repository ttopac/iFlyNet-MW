# This script can be used to plot several sensor signals in real-time.
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import StrainGageBridgeType
from nidaqmx import stream_readers
from nidaqmx import Task

import numpy as np
from scipy.signal import resample
import time
import math

import tkinter as tk
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from capture_SG_offsets import send_SG_offsets
from capture_data import send_data
from multiprocessing import Process, Queue, Pipe
from concurrent.futures import ThreadPoolExecutor

#Initialize the DAQ and SG parameters
params = dict()
params["sample_rate"] = 7000
SGcoeffs = dict()
SGcoeffs["amplifier_coeff"] = 100
SGcoeffs["GF"] = 2.11
SGcoeffs["Vex"] = 12
downsample_mult = 1

#Plotting coefficients
plot_refresh_rate = 0.5 #seconds
visible_duration = 60 #seconds
num_samples = int(params["sample_rate"]*plot_refresh_rate/downsample_mult)

#Initialize the GUI
root = tk.Tk()
root.title ("Real-time Plotting")

#Initialize the plot:
plt.style.use ('fivethirtyeight')
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#bcbd22', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#17becf', '#d62728']) 
mpl.rcParams['axes.edgecolor'] = 'black'
mpl.rcParams['axes.linewidth'] = 1

fig = plt.figure(figsize=(6, 4.0))
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
fig.tight_layout(pad=2.0)
xs = np.linspace (0, visible_duration, int(visible_duration*params["sample_rate"]/downsample_mult))
ys = np.zeros((16,int(visible_duration*params["sample_rate"]/downsample_mult)))

PZTlines = list()
for i in range(6):
  PZTlines.append(ax1.plot(xs, ys[i], linewidth=0.3, label="PZT {}".format(i+1))[0])
ax1.set_xlim(0, visible_duration)
ax1.set_ylim(-0.1, 0.1)
leg1 = ax1.legend(fontsize=7, loc="upper right", ncol=2, columnspacing=1)
for line in leg1.get_lines():
  line.set_linewidth(1.5)
ax1.set_title("PZT data", fontsize=12)
ax1.set_xlabel("Time", fontsize=11)
ax1.set_ylabel("Signal (V)", labelpad=1, fontsize=11)
ax1.set_xticklabels([])
ax1.tick_params(labelsize="small")

SGlines = list()
for i in range(8):
  SGlines.append(ax2.plot(xs, ys[6+i], linewidth=0.3, label="SG {}".format(i+1))[0])
liftline, = ax2.plot(xs, ys[14], linewidth=0.5, label="Lift")
dragline, = ax2.plot(xs, ys[15], linewidth=0.5, label="Drag")
ax2.set_xlim(0, visible_duration)
ax2.set_ylim(-100, 100)
leg2 = ax2.legend(fontsize=7, loc="upper right", ncol=4, columnspacing=1)
for line in leg2.get_lines():
  line.set_linewidth(1.5)
ax2.set_title("SG data", fontsize=12)
ax2.set_xlabel("Time", fontsize=11)
ax2.set_ylabel("Strain (us)", labelpad=-2, fontsize=11)
ax2.set_xticklabels([])
ax2.tick_params(labelsize="small")


#Function to generate real-time plots.
def plot_live(i, ys):
  global read_data
  global start
  if (i%int(visible_duration/plot_refresh_rate) == 0):
    ys [:,:] = 0
  
  fewerdata = resample(read_data, num_samples, axis=1) #Downsample the data
  slice_start = i%(int(visible_duration/plot_refresh_rate))*num_samples
  slice_end = i%(int(visible_duration/plot_refresh_rate))*num_samples + num_samples
  ys[:,slice_start:slice_end] = fewerdata 
  
  for count,line in enumerate(PZTlines):
    line.set_ydata(ys[count])
  for count,line in enumerate(SGlines):
    line.set_ydata(ys[count+6])
  liftline.set_ydata(ys[14])
  dragline.set_ydata(ys[15])
  # return list((liftline,dragline))+PZTlines+SGlines
  return list((liftline,))+PZTlines+SGlines

if __name__ == "__main__":
  global read_data
  global start

  # Get strain gauge offsets for calibration
  parent_conn, child_conn = Pipe()
  p = Process(target = send_SG_offsets, args=(child_conn,))
  p.start()
  SGoffsets = parent_conn.recv()
  p.join()

  # Run capture data in background
  executor = ThreadPoolExecutor(max_workers=4)
  executor.submit(send_data, SGoffsets, 700, "continuous")
  time.sleep(0.5)
  from capture_data import read_data

  # Plot the data
  canvas = FigureCanvasTkAgg(fig, master=root)
  canvas.get_tk_widget().grid(column=0, row=1)
  start = time.time()
  ani = FuncAnimation(fig, plot_live, fargs=(ys,), interval=plot_refresh_rate*1000, blit=True)
  root.mainloop()


