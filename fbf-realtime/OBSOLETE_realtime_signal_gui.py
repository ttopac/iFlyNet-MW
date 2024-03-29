# THIS SCRIPT IS NOW OBSELETE. USE SIGNAL_SHAPE_GUI INSTEAD.

# This script can be used to plot several sensor signals in real-time.
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from threading import Thread
from multiprocessing import Process, Queue

import sys
import os
sys.path.append(os.path.abspath('./fbf-DAQ'))
sys.path.append(os.path.abspath('./helpers'))
import daq_captureSGoffsets_helper
import daq_capturedata_helper
import plot_sensordata_helper


#Initialize the DAQ and SG parameters
params = dict()
params["sample_rate"] = 1700 #This will not be the actual sampling rate. NI uses sampling rate of something around for this input 1724.

#Plotting coefficients and initializer
visible_duration = 30 #seconds
plot_refresh_rate = 1 #seconds
downsample_mult = 1
ys = np.zeros((16,int(visible_duration*params["sample_rate"]/downsample_mult)))

#Initialize the GUI
root = tk.Tk()
root.title ("Real-time Plotting")

if __name__ == "__main__":
  # Get strain gauge offsets for calibration
  q1 = Queue()
  p1 = Thread(target = daq_captureSGoffsets_helper.send_SG_offsets, args=(params["sample_rate"], int(params["sample_rate"]), q1))
  p1.start()
  SGoffsets = q1.get()
  p1.join()

  # Run capture data in background
  q2 = Queue()
  p2 = Process(target = daq_capturedata_helper.send_data, args=(SGoffsets, params["sample_rate"], int(params["sample_rate"]*plot_refresh_rate), "continuous", q2))
  p2.start()

  # Plot the data
  plot = plot_sensordata_helper.PlotSensorData(visible_duration, downsample_mult, params)
  plot.plot_raw_lines(realtime=True, plot_refresh_rate=plot_refresh_rate)
  plot.term_common_params(realtime=True)

  canvas = FigureCanvasTkAgg(plot.fig, master=root)
  canvas.get_tk_widget().grid(column=0, row=1)
  ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(ys,q2,plot_refresh_rate), interval=plot_refresh_rate*1000, blit=True)
  root.mainloop()
  
