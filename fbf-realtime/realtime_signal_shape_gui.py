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
from plot_sensordata_helper import PlotSensorData
from daq_capturevideo_helper import DrawTKVideoCapture
from proc_MFCshape_helper import CalcMFCShape
from plot_MFC_helper import PlotMFCShape

#Plotting in TK class
class RawSignalAndShapeWindow(Frame):
  def __init__(self, parent=None):
    Frame.__init__(self,parent)
    self.parent = parent
    self.grid()
    for r in range(4):
      self.parent.rowconfigure(r, weight=1)    
    for c in range(2):
      self.parent.columnconfigure(c, weight=1)

  def draw_videos(self, video_names, camnums):
    video1 = DrawTKVideoCapture(self.parent, video_names[0], camnums[0])
    video1.videolbl.grid(row=1, column=0, rowspan=1, columnspan=1, sticky=S)
    video1.videocvs.grid(row=2, column=0, rowspan=1, columnspan=1, sticky=N)
    video1.multithreaded_capture(init_call=True) #Use for multi-threaded executions
    # video1.update() #Use for single threaded executions

    video2 = DrawTKVideoCapture(self.parent, video_names[1], camnums[1])
    video2.videolbl.grid(row=14, column=0, rowspan=1, columnspan=1, pady=5, sticky=S)
    video2.videocvs.grid(row=15, column=0, rowspan=1, columnspan=1, sticky=N)
    video2.multithreaded_capture(init_call=True) #Use for multi-threaded executions
    # video2.update() #Use for single threaded executions

  def getSGoffsets (self, params):
    #Capture SG offsets:
    q1 = Queue()
    p1 = Thread(target = send_SG_offsets, args=(params["sample_rate"], int(params["sample_rate"]), q1))
    p1.start()
    self.SGoffsets = q1.get()
    p1.join()

  def plot_signals(self, ys, visible_duration, downsample_mult, params, plot_refresh_rate, plot_compensated_strains=False, onlyplot=True):
    # Run capture data in background
    self.data_queue = Queue()
    get_data_proc = Process(target = send_data, args=(self.SGoffsets, params["sample_rate"], int(params["sample_rate"]*plot_refresh_rate), "continuous", self.data_queue))
    get_data_proc.start()
    # Plot the data
    plot = PlotSensorData(visible_duration, downsample_mult, params)
    plot.plot_raw_lines(realtime=True, plot_refresh_rate=plot_refresh_rate)
    plot.term_common_params(realtime=True)
    canvas = FigureCanvasTkAgg(plot.fig, master=self.parent)
    canvas.get_tk_widget().grid(row=1, column=1, rowspan=13, columnspan=1)
    ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(ys,self.data_queue,plot_refresh_rate,plot_compensated_strains,onlyplot), interval=plot_refresh_rate*1000, blit=True) #THIS DOESN'T REMOVE FROM DATA_QUEUE
    self.update()

  def draw_MFCshapes(self, params, plot_refresh_rate):    
    #Only have this section enabled MFCshapes is alone
    # self.data_queue = Queue()
    # get_data_proc = Process(target = send_data, args=(self.SGoffsets, params["sample_rate"], int(params["sample_rate"]*plot_refresh_rate), "continuous", self.data_queue))
    # get_data_proc.start()
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
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.2 #seconds
  downsample_mult = 1
  ys = np.zeros((16,int(visible_duration*params["sample_rate"]/downsample_mult)))
  video_names = ("Side-view of wing fixture", "Side view of the outer MFC")
  camnums = (1,2)
  
  root = Tk()
  root.title ("Real-time Raw Signal and Estimated Shape")
  # root.geometry("1000x1200")

  app = RawSignalAndShapeWindow(parent=root)
  app.getSGoffsets(params)
  app.draw_videos(video_names, camnums)
  app.plot_signals(ys, visible_duration, downsample_mult, params, plot_refresh_rate, plot_compensated_strains=False, onlyplot=False)
  app.draw_MFCshapes(params, plot_refresh_rate)
  root.mainloop()