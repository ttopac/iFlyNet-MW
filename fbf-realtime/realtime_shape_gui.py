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
import daq_captureSGoffsets_helper
import daq_capturedata_helper
import proc_MFCshape_helper
import plot_MFC_helper

#Plotting in TK class
class ShapeWindow(Frame):
  def __init__(self, parent=None):
    Frame.__init__(self,parent)
    self.parent = parent

  def getSGoffsets (self, params):
    #Capture SG offsets:
    q1 = Queue()
    p1 = Thread(target = daq_captureSGoffsets_helper.send_SG_offsets, args=(params["sample_rate"], int(params["sample_rate"]), q1))
    p1.start()
    self.SGoffsets = q1.get()
    p1.join()

  def draw_MFCshapes(self, params, plot_refresh_rate, plot_type, blit):    
    #Only have this section enabled when MFCshapes is alone
    self.data_queue = Queue()
    get_data_proc = Process(target = daq_capturedata_helper.send_data, args=(self.SGoffsets, params["sample_rate"], int(params["sample_rate"]*plot_refresh_rate), "continuous", self.data_queue))
    get_data_proc.start()
    ###

    mfc_shape = proc_MFCshape_helper.CalcMFCShape(plot_refresh_rate)
    shape_queue = Queue()
    p2 = Process(target = mfc_shape.supply_data, args=(shape_queue, self.data_queue, False)) #THIS REMOVES FROM DATA_QUEUE
    p2.start()

    plot = plot_MFC_helper.PlotMFCShape(plot_refresh_rate, mfc_shape.XVAL, mfc_shape.YVAL)
    plot.init_plot(plot_type)
    mfc_lbl = Label(self.parent, text="Shape of morphing trailing edge section", font=("Helvetica", 16))
    mfc_lbl.grid(row=14, column=1, rowspan=1, columnspan=1, sticky=S)
    mfc_canvas = FigureCanvasTkAgg(plot.fig, master=self.parent)
    mfc_canvas.get_tk_widget().grid(row=15, column=1, rowspan=1, columnspan=1, sticky=N)
    ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(shape_queue, plot_type, blit), interval=plot_refresh_rate*1000, blit=blit)
    self.update()


if __name__ == "__main__":
  #Define parameters
  params = dict()
  params["sample_rate"] = 1700 #This will not be the actual sampling rate. NI uses sampling rate of something around for this input 1724.
  plot_refresh_rate = 0.1 #seconds
  
  root = Tk()
  root.title ("Real-time Estimated Shape")

  app = ShapeWindow(parent=root)
  app.getSGoffsets(params)
  app.draw_MFCshapes(params, plot_refresh_rate, 'contour', True)
  root.mainloop()