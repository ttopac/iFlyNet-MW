import numpy as np
from tkinter import *
from tkinter import Tk, Frame, Button
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from threading import Thread
from multiprocessing import Process, Queue

import time
import sys
import os
sys.path.append(os.path.abspath('./fbf-DAQ'))
sys.path.append(os.path.abspath('./helpers'))
from daq_captureSGoffsets_helper import send_SG_offsets
from daq_capturedata_helper import send_data
from proc_MFCshape_helper import CalcMFCShape
from plot_MFC_helper import PlotMFCShape

#Plotting in TK class
class ShapeWindow(Frame):
  def __init__(self, parent=None):
    Frame.__init__(self,parent)
    self.parent = parent

  def getSGoffsets (self, params):
    #Capture SG offsets:
    q1 = Queue()
    p1 = Thread(target = send_SG_offsets, args=(params["sample_rate"], int(params["sample_rate"]), q1))
    p1.start()
    self.SGoffsets = q1.get()
    p1.join()

  def draw_MFCshapes(self, params, plot_refresh_rate):    
    #Only have this section enabled MFCshapes is alone
    self.data_queue = Queue()
    get_data_proc = Process(target = send_data, args=(self.SGoffsets, params["sample_rate"], int(params["sample_rate"]*plot_refresh_rate), "continuous", self.data_queue))
    get_data_proc.start()
    ###

    mfc_shape = CalcMFCShape(plot_refresh_rate)
    shape_queue = Queue()
    p2 = Process(target = mfc_shape.supply_data, args=(shape_queue, self.data_queue, False)) #THIS REMOVES FROM DATA_QUEUE
    p2.start()

    plot = PlotMFCShape(plot_refresh_rate, mfc_shape.XVAL, mfc_shape.YVAL)
    plot.plot_twod_contour()

    mfc_lbl = Label(self.parent, text="Shape of morphing trailing edge section", font=("Helvetica", 16))
    mfc_lbl.grid(row=14, column=1, rowspan=1, columnspan=1, pady=5, sticky=S)
    mfc_canvas = FigureCanvasTkAgg(plot.fig, master=self.parent)
    mfc_canvas.get_tk_widget().grid(row=15, column=1, rowspan=1, columnspan=1, sticky=N)
    ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(shape_queue,), interval=plot_refresh_rate*1000, blit=False)
    self.update()


if __name__ == "__main__":
  #Define parameters
  params = dict()
  params["sample_rate"] = 1700 #This will not be the actual sampling rate. NI uses sampling rate of something around for this input 1724.
  plot_refresh_rate = 1 #seconds
  
  root = Tk()
  root.title ("Real-time Estimated Shape")

  app = ShapeWindow(parent=root)
  app.getSGoffsets(params)
  app.draw_MFCshapes(params, plot_refresh_rate)
  root.mainloop()