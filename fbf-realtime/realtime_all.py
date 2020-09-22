import numpy as np
from tkinter import *
from tkinter import Tk, Frame, Button, Label
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
import plot_sensordata_helper
import daq_capturevideo_helper
import proc_MFCshape_helper
import plot_MFC_helper
import plot_commSGs_westimates_helper
import proc_keras_estimates_helper

#Plotting in TK class
class GroundTruthAndiFlyNetEstimatesWindow(Frame):
  def __init__(self, parent=None):
    Frame.__init__(self,parent)
    self.parent = parent
    self.stall_cond = "No"
    self.truth_lift_val = 0
    self.truth_drag_val = 0
    self.est_lift_val = 0
    self.est_drag_val = 0
    self.grid()

  def draw_titlelabels (self, labels):
    self.lbl1 = Label(self.parent, text=labels[0], font=("Helvetica", 18, 'bold', 'underline'), justify='center')
    self.lbl1.grid(row=0, column=0, rowspan=1, columnspan=3, sticky=S)
    self.lbl2 = Label(self.parent, text=labels[1], font=("Helvetica", 18, 'bold', 'underline'), justify='center')
    self.lbl2.grid(row=0, column=3, rowspan=1, columnspan=3, sticky=S)

  def draw_videos(self, video_names, camnums):
    video1 = daq_capturevideo_helper.DrawTKVideoCapture(self.parent, video_names[0], camnums[0])
    video1.videolbl.grid(row=1, column=2, rowspan=1, columnspan=1)
    video1.videocvs.grid(row=1, column=0, rowspan=1, columnspan=2)
    video1.multithreaded_capture(init_call=True) #Use for multi-threaded executions
    # video1.update() #Use for single threaded executions

    video2 = daq_capturevideo_helper.DrawTKVideoCapture(self.parent, video_names[1], camnums[1])
    video2.videolbl.grid(row=3, column=2, rowspan=1, columnspan=1)
    video2.videocvs.grid(row=3, column=0, rowspan=1, columnspan=2)
    video2.multithreaded_capture(init_call=True) #Use for multi-threaded executions
    # video2.update() #Use for single threaded executions

  def getSGoffsets (self, params):
    #Capture SG offsets:
    q1 = Queue()
    p1 = Thread(target = send_SG_offsets, args=(params["sample_rate"], int(params["sample_rate"]), q1))
    p1.start()
    self.SGoffsets = q1.get()
    p1.join()

  def captureData (self, params, plot_refresh_rate):
    # Run capture data in background
    self.data_queue = Queue()
    get_data_proc = Process(target = send_data, args=(self.SGoffsets, params["sample_rate"], int(params["sample_rate"]*plot_refresh_rate), "continuous", self.data_queue))
    get_data_proc.start()

  def draw_MFCshapes(self, params, plot_refresh_rate):    
    mfc_shape = proc_MFCshape_helper.CalcMFCShape(plot_refresh_rate)
    shape_queue = Queue()
    p2 = Process(target = mfc_shape.supply_data, args=(shape_queue, self.data_queue, False)) #THIS REMOVES FROM DATA QUEUE
    p2.start()

    plot = plot_MFC_helper.PlotMFCShape(plot_refresh_rate, mfc_shape.XVAL, mfc_shape.YVAL)
    plot.plot_twod_contour()

    mfc_lbl = Label(self.parent, text="Morphing section shape", font=("Helvetica", 16))
    mfc_lbl.grid(row=3, column=3, rowspan=1, columnspan=1)
    mfc_canvas = FigureCanvasTkAgg(plot.fig, master=self.parent)
    mfc_canvas.get_tk_widget().grid(row=3, column=4, rowspan=1, columnspan=2)
    ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(shape_queue,), interval=plot_refresh_rate*1000, blit=False)
    self.update()

  def draw_stall_lbl (self):
    stall_lbl = Label(self.parent, text='Stall?', font=("Helvetica", 16), justify='center')
    stall_lbl.grid(row=1, column=3, rowspan=1, columnspan=1)
    stall_cond_lbl = Label(self.parent, text=self.stall_cond, font=("Arial", 26), justify='center')
    stall_cond_lbl.grid(row=1, column=4, rowspan=1, columnspan=1)

  def draw_liftdrag_lbl (self):
    liftdrag_truth_lbl = Label(self.parent, text='L = {} ue \n D = {} ue'.format(self.truth_lift_val, self.truth_drag_val), font=("Helvetica", 24), justify='center')
    liftdrag_truth_lbl.grid(row=2, column=1, rowspan=1, columnspan=1)
    liftdrag_est_lbl = Label(self.parent, text='L = {} ue \n D = {} ue'.format(self.est_lift_val, self.est_drag_val), font=("Helvetica", 24), justify='center')
    liftdrag_est_lbl.grid(row=2, column=4, rowspan=1, columnspan=1)  

  def initialize_estimates (self, pred_freq, stall_model_path, liftdrag_model_path, plot_refresh_rate, temperature_compensation=False):
    self.estimates = proc_keras_estimates_helper.iFlyNetEstimates(pred_freq, stall_model_path, liftdrag_model_path)
    self.stallest_queue = Queue()
    self.liftdragest_queue = Queue()
    p_estimations = Process(target = self.update_estimations, args=(plot_refresh_rate,)) #THIS REMOVES FROM DATA_QUEUE
    p_estimations.start()

  def update_estimations(self, plot_refresh_rate):
    while True:
      try:
        read_data = self.data_queue.get()
        self.data_queue.put_nowait(read_data) #THIS DOESN'T REMOVE FROM DATA QUEUE
        stall_predictors = np.concatenate ((read_data[0:6], read_data[14:16]), axis=0)
        self.stallest_queue.put (self.estimates.estimate_stall(stall_predictors[:,-keras_samplesize:], True))
        liftdrag_predictors = read_data[0:6]
        self.liftdragest_queue.put (self.estimates.estimate_liftdrag(liftdrag_predictors[:,-keras_samplesize:], True))
      except:
        pass
      time.sleep(plot_refresh_rate)

  def update_stallest_lbls (self, plot_refresh_rate):
    stall_cond = self.stallest_queue.get() #THIS REMOVES FROM STALLEST QUEUE
    self.stall_cond_lbl.set(stall_cond)
    self.parent.after(plot_refresh_rate, self.update_stallest_lbls)

  def update_liftdrag_lbls (self, plot_refresh_rate):
    try:
      read_data = self.data_queue.get() #THIS DOESN'T REMOVE FROM DATA QUEUE
      self.data_queue.put_nowait(read_data)
      truth_liftdrag = read_data[14:16]
      self.truth_lift_val.set(truth_liftdrag[0])
      self.truth_drag_val.set(truth_liftdrag[1])

      est_liftdrag = self.liftdragest_queue.get() #THIS REMOVES FROM LIFTDRAGEST QUEUE
      self.est_lift_val.set(est_liftdrag[0])
      self.est_drag_val.set(est_liftdrag[1])
    except:
      pass
    self.parent.after(plot_refresh_rate, self.update_liftdrag_lbls)

  def draw_liftdrag_plots(self, ys, visible_duration, downsample_mult, params, plot_refresh_rate, pred_freq, stall_model_path, liftdrag_model_path, plot_compensated_strains, onlyplot):
    truthplot = plot_commSGs_westimates_helper.PlotData(0, pred_freq, stall_model_path, liftdrag_model_path, singleplot=True, realtime=True) #xs=0 is just a placeholder here
    truthplot.init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate)
    truthplot.plot_liftdrag(ys)
    truthplot.term_common_params()
    truthplot_lbl = Label(self.parent, text='Lift/Drag', font=("Helvetica", 16), justify='center')
    truthplot_lbl.grid(row=2, column=2, rowspan=2, columnspan=1)
    truth_canvas = FigureCanvasTkAgg(truthplot.fig, master=self.parent)
    truth_canvas.get_tk_widget().grid(row=2, column=0, rowspan=1, columnspan=1)
    truth_ani = FuncAnimation(truthplot.fig, truthplot.plot_live, fargs=(ys,self.data_queue,plot_refresh_rate,plot_compensated_strains,onlyplot,False), interval=plot_refresh_rate*1000, blit=True) #THIS DOESN'T REMOVE FROM DATA QUEUE
    
    estplot = plot_commSGs_westimates_helper.PlotData(0, pred_freq, stall_model_path, liftdrag_model_path, singleplot=True, realtime=True) #xs=0 is just a placeholder here
    estplot.init_realtime_params(self, visible_duration, downsample_mult, params, plot_refresh_rate)
    estplot.plot_liftdrag(ys)
    estplot.term_common_params()
    estplot_lbl = Label(self.parent, text='Lift/Drag', font=("Helvetica", 16), justify='center')
    estplot_lbl.grid(row=2, column=3, rowspan=1, columnspan=1)
    est_canvas = FigureCanvasTkAgg(truthplot.fig, master=self.parent)
    est_canvas.get_tk_widget().grid(row=2, column=5, rowspan=1, columnspan=1)
    est_ani = FuncAnimation(estplot.fig, estplot.plot_live, fargs=(ys,self.liftdragest_queue,plot_refresh_rate,plot_compensated_strains, onlyplot,True), interval=plot_refresh_rate*1000, blit=True) #THIS DOESN'T REMOVE FROM LIFTDRAGEST QUEUE

    self.update()


if __name__ == "__main__":
  #Define parameters
  params = dict()
  params["sample_rate"] = 1700 #This will not be the actual sampling rate. NI uses sampling rate of something around for this input 1724.
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.1 #seconds
  downsample_mult = 1
  plot_compensated_strains = False
  onlyplot = False
  
  title_labels = ("Measurements (ground truth)", "i-FlyNet Estimates")

  ys = np.zeros((2,int(visible_duration*params["sample_rate"]/downsample_mult)))
  video_names = ("AoA view", "Outer MFC view")
  camnums = (1,2)

  stall_model_filename = 'stall_train993_val_988'
  liftdrag_model_filename = 'lift_train_loss0461'
  keras_samplesize=233 #This is also used for pred_freq. Bad naming here.
  stall_model_path = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Kerasfiles/{}.hdf5'.format(stall_model_filename)
  liftdrag_model_path = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Kerasfiles/{}.hdf5'.format(liftdrag_model_filename)
  
  root = Tk()
  root.title ("Real-time Ground Truth and i-FlyNet Estimation")
  # root.geometry("1000x1200")

  app = GroundTruthAndiFlyNetEstimatesWindow(parent=root)
  app.getSGoffsets(params)
  app.draw_titlelabels()
  app.draw_videos(video_names, camnums)
  app.captureData(params, plot_refresh_rate)
  app.initialize_estimates(keras_samplesize, stall_model_path, liftdrag_model_path, plot_refresh_rate)
  
  app.draw_stall_lbl()
  app.draw_liftdrag_lbl()
  app.update_stallest_lbls(plot_refresh_rate)
  app.update_liftdrag_lbls(plot_refresh_rate)

  app.draw_MFCshapes(params, plot_refresh_rate)
  app.draw_liftdrag_plots(ys, visible_duration, downsample_mult, params, plot_refresh_rate, plot_refresh_rate, stall_model_path, liftdrag_model_path, plot_compensated_strains, onlyplot)
  root.mainloop()