# This script can be used to plot several sensor signals in real-time.
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from multiprocessing import Process, Queue, Pipe

import sys
import os
sys.path.append(os.path.abspath('./fbf-DAQ'))
sys.path.append(os.path.abspath('./helpers'))
from capture_SG_offsets import send_SG_offsets
from capture_data import send_data
from plot_realtime_helper import PlotRealtime


#Initialize the DAQ and SG parameters
params = dict()
params["sample_rate"] = 1700 #This will not be the actual sampling rate. NI uses sampling rate of something around for this input 1724.
SGcoeffs = dict()
SGcoeffs["amplifier_coeff"] = 100
SGcoeffs["GF"] = 2.11
SGcoeffs["Vex"] = 12

#Plotting coefficients
visible_duration = 30 #seconds
plot_refresh_rate = 1 #seconds
downsample_mult = 1

#Initialize the GUI
root = tk.Tk()
root.title ("Real-time Plotting")

#Run animation
def run_animate(ys, q2):
  realtime_plot = PlotRealtime(params, visible_duration, plot_refresh_rate, downsample_mult)
  canvas = FigureCanvasTkAgg(realtime_plot.fig, master=root)
  canvas.get_tk_widget().grid(column=0, row=1)
  ani = FuncAnimation(realtime_plot.fig, realtime_plot.plot_live, fargs=(ys,q2), interval=plot_refresh_rate*1000, blit=True)
  root.mainloop()

if __name__ == "__main__":
  # Get strain gauge offsets for calibration
  q1 = Queue()
  p1 = Process(target = send_SG_offsets, args=(params["sample_rate"], int(params["sample_rate"]), q1))
  p1.start()
  SGoffsets = q1.get()
  p1.join()

  # Run capture data in background
  q2 = Queue()
  p1 = Process(target = send_data, args=(SGoffsets, params["sample_rate"], int(params["sample_rate"]*plot_refresh_rate), "continuous", q2))
  p1.start()

  # Plot the data
  ys = np.zeros((16,int(visible_duration*params["sample_rate"]/downsample_mult)))
  p2 = Process(target = run_animate, args=(ys,q2))
  p2.start()
  
