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

from numpy.lib.npyio import save
sys.path.append(os.path.abspath('./fbf-DAQ'))
sys.path.append(os.path.abspath('./helpers'))
import daq_captureSGoffsets_helper
import daq_capturedata_helper
import plot_sensordata_helper
import daq_capturevideo_helper
import proc_MFCshape_helper
import plot_MFC_helper

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
    video1 = daq_capturevideo_helper.DrawTKVideoCapture(self.parent, video_names[0], camnums[0])
    video1.videolbl.grid(row=1, column=0, rowspan=1, columnspan=1, sticky=S)
    video1.videocvs.grid(row=2, column=0, rowspan=1, columnspan=1, sticky=N)
    self.video1 = video1
    self.t1 = Thread(target=video1.multithreaded_capture, args=(33, True))
    # video1.capture() #Use for single threaded executions

    video2 = daq_capturevideo_helper.DrawTKVideoCapture(self.parent, video_names[1], camnums[1])
    video2.videolbl.grid(row=14, column=0, rowspan=1, columnspan=1, pady=5, sticky=S)
    video2.videocvs.grid(row=15, column=0, rowspan=1, columnspan=1, sticky=N)
    self.video2 = video2
    self.t2 = Thread(target=video2.multithreaded_capture, args=(33, True))
    # video2.capture() #Use for single threaded executions

    self.t1.start()
    self.t2.start()
    self.update()

  def getSGoffsets (self, params):
    #Capture SG offsets:
    q1 = Queue()
    p1 = Thread(target = daq_captureSGoffsets_helper.send_SG_offsets, args=(params["sample_rate"], int(params["sample_rate"]), q1))
    p1.start()
    self.SGoffsets = q1.get()
    p1.join()

  def plot_signals(self, ys, visible_duration, downsample_mult, params, plot_refresh_rate, onlyplot, plot_compensated_strains=False, saveflag_queue=None, save_duration=0, saver=None):
    # Run capture data in background
    self.data_queue = Queue()
    self.saveflag_queue = Queue()
    self.get_data_proc = Process(target = daq_capturedata_helper.send_data, args=(self.SGoffsets, params["sample_rate"], int(params["sample_rate"]*plot_refresh_rate), "continuous", self.data_queue, saveflag_queue, save_duration, saver))
    self.get_data_proc.start()
    
    # Plot the data
    plot = plot_sensordata_helper.PlotSensorData(visible_duration, downsample_mult, params)
    plot.plot_raw_lines(realtime=True, plot_refresh_rate=plot_refresh_rate)
    plot.term_common_params(realtime=True)
    canvas = FigureCanvasTkAgg(plot.fig, master=self.parent)
    canvas.get_tk_widget().grid(row=1, column=1, rowspan=13, columnspan=1)
    ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(ys, self.data_queue, plot_refresh_rate, plot_compensated_strains, onlyplot), interval=plot_refresh_rate*1000, blit=True) #THIS DOESN'T REMOVE FROM DATA_QUEUE
    self.update()

  def draw_MFCshapes(self, plot_refresh_rate, plot_type, blit):    
    mfc_shape = proc_MFCshape_helper.CalcMFCShape(plot_refresh_rate)
    self.shape_queue = Queue()
    self.draw_MFC_proc = Process(target = mfc_shape.supply_data, args=(self.shape_queue, self.data_queue, False)) #THIS REMOVES FROM DATA_QUEUE
    self.draw_MFC_proc.start()

    plot = plot_MFC_helper.PlotMFCShape(plot_refresh_rate, mfc_shape.XVAL, mfc_shape.YVAL)
    plot.init_plot(plot_type)
    mfc_lbl = Label(self.parent, text="Shape of morphing trailing edge section", font=("Helvetica", 16))
    mfc_lbl.grid(row=14, column=1, rowspan=1, columnspan=1, sticky=S)
    mfc_canvas = FigureCanvasTkAgg(plot.fig, master=self.parent)
    mfc_canvas.get_tk_widget().grid(row=15, column=1, rowspan=1, columnspan=1, sticky=N)
    ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(self.shape_queue, plot_type, blit), interval=plot_refresh_rate*1000, blit=blit)
    self.update()


if __name__ == "__main__":
  #Define parameters
  params = dict()
  params["sample_rate"] = 1700 #NI uses sample rate values around this, not exactly this.
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.2 #seconds
  downsample_mult = 1
  ys = np.zeros((17,int(visible_duration*params["sample_rate"]/downsample_mult)))
  video_titles = ("Side view of the outer MFC", "Side view of the wing fixture")
  camnums = (1,0)

  #Start the GUI  
  root = Tk()
  root.title ("Real-time Raw Signal and Estimated Shape")

  app = RawSignalAndShapeWindow(parent=root)
  app.getSGoffsets(params)
  app.draw_videos(video_titles, camnums)
  app.plot_signals(ys, visible_duration, downsample_mult, params, plot_refresh_rate, onlyplot=False, plot_compensated_strains=False)
  app.draw_MFCshapes(plot_refresh_rate, "surface", False)
  root.mainloop()