import numpy as np
from tkinter import *
from tkinter import Tk, Frame, Button, Label, Canvas
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
import daq_capturevideo_helper
import proc_MFCshape_helper
import plot_MFC_helper
import plot_commSGs_westimates_helper
import proc_keras_estimates_helper

#Plotting in TK class
class GroundTruthAndiFlyNetEstimatesWindow(Frame):
  def __init__(self, parent, plot_refresh_rate, downsample_mult):
    Frame.__init__(self,parent)
    self.parent = parent
    self.stall_cond = "No"
    self.truth_lift_val = 0
    self.truth_drag_val = 0
    self.est_lift_val = 0
    self.est_drag_val = 0
    self.plot_refresh_rate = plot_refresh_rate
    self.downsample_mult = downsample_mult

  def init_UI (self, labels):
    self.lbl1 = Label(self.parent, text=labels[0], font=("Helvetica", 21, 'bold', 'underline'), justify='center')
    self.lbl1.grid(row=0, column=0, rowspan=1, columnspan=3, sticky=S)
    self.lbl2 = Label(self.parent, text=labels[1], font=("Helvetica", 21, 'bold', 'underline'), justify='center')
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

  def captureData (self, params):
    # Run capture data in background
    self.data_queue = Queue()
    get_data_proc = Process(target = send_data, args=(self.SGoffsets, params["sample_rate"], int(params["sample_rate"]*self.plot_refresh_rate), "continuous", self.data_queue))
    get_data_proc.start()

  def draw_MFCshapes(self):    
    mfc_shape = proc_MFCshape_helper.CalcMFCShape(self.plot_refresh_rate)
    self.shape_queue = Queue()
    p2 = Process(target = mfc_shape.supply_data, args=(self.shape_queue, self.data_queue, False)) #THIS DOESN'T REMOVE FROM DATA QUEUE
    p2.start()

    plot = plot_MFC_helper.PlotMFCShape(self.plot_refresh_rate, mfc_shape.XVAL, mfc_shape.YVAL)
    plot.plot_twod_contour()

    mfc_lbl = Label(self.parent, text="Morphing\nsection shape", font=("Helvetica", 18), justify='center')
    mfc_lbl.grid(row=3, column=3, rowspan=1, columnspan=1, padx=65)
    mfc_canvas = FigureCanvasTkAgg(plot.fig, master=self.parent)
    mfc_canvas.get_tk_widget().grid(row=3, column=4, rowspan=1, columnspan=2, sticky=W)
    ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(self.shape_queue,), interval=self.plot_refresh_rate*1000, blit=False)
    
    # t_qlens = Thread(target = self.print_queuelens)
    # t_qlens.start()
    self.update()

  def draw_stall_lbl (self):
    stall_lbl = Label(self.parent, text='Stall?', font=("Helvetica", 18), justify='center')
    stall_lbl.grid(row=1, column=3, rowspan=1, columnspan=1)
    self.stall_cond_lbl = Label(self.parent, text=self.stall_cond, font=("Arial", 26), justify='center')
    self.stall_cond_lbl.grid(row=1, column=4, rowspan=1, columnspan=1, sticky=W)

  def draw_liftdrag_lbl (self):
    self.liftdrag_truth_lbl = Label(self.parent, text='Lift SG = {} ue \n Drag SG = {} ue'.format(self.truth_lift_val, self.truth_drag_val), font=("Helvetica", 16), width=20)
    self.liftdrag_truth_lbl.grid(row=2, column=1, rowspan=1, columnspan=1, sticky=W)
    self.liftdrag_est_lbl = Label(self.parent, text='Lift SG = {} ue \n Drag SG = {} ue'.format(self.est_lift_val, self.est_drag_val), font=("Helvetica", 16), width=20)
    self.liftdrag_est_lbl.grid(row=2, column=4, rowspan=1, columnspan=1, sticky=W)  

  def initialize_estimates (self, pred_freq, stall_model_path, liftdrag_model_path, plot_refresh_rate, temperature_compensation=False):
    self.estimates = proc_keras_estimates_helper.iFlyNetEstimates(pred_freq, stall_model_path, liftdrag_model_path)
    self.stallest_queue = Queue()
    self.liftdragest_queue = Queue()
    t_estimations = Thread(target = self.update_estimations) #THIS DOESN'T REMOVE FROM DATA_QUEUE
    t_estimations.start()

  def update_estimations(self):
    while True:
      try:
        read_data = self.data_queue.get_nowait() #THIS REMOVES FROM DATA QUEUE
        useful_data_start, useful_data_end = 0, int(read_data.shape[1]/self.downsample_mult)*self.downsample_mult
        stall_predictors = np.concatenate ((read_data[0:6], read_data[14:16]), axis=0)
        self.stallest_queue.put_nowait (np.any(self.estimates.estimate_stall(stall_predictors[:,useful_data_start:useful_data_end])))
        liftdrag_predictors = read_data[0:6]
        self.liftdragest_queue.put_nowait (self.estimates.estimate_liftdrag(liftdrag_predictors[:,useful_data_start:useful_data_end]))
      except:
        pass
      time.sleep(self.plot_refresh_rate)

  def update_stallest_lbls (self):
    while self.stallest_queue.qsize() > 1: #This is here to keep up with delay in plotting.
      try:  
        a = self.stallest_queue.get_nowait()
      except:
        pass
    try:
      stall_cond = self.stallest_queue.get_nowait() #THIS REMOVES FROM STALLEST QUEUE
      stalltext = "Yes" if stall_cond else "No"
      self.stall_cond_lbl.config(text=stalltext)
    except:
      pass
    self.parent.after(int(self.plot_refresh_rate*1000), self.update_stallest_lbls)

  def update_liftdrag_lbls (self):
    while self.liftdragest_queue.qsize() > 1: #This is here to keep up with delay in plotting.
      try:
        a = self.liftdragest_queue.get_nowait()
      except:
        pass
    try:
      est_liftdrag = self.liftdragest_queue.get_nowait() #THIS REMOVES FROM LIFTDRAGEST QUEUE
      self.liftdrag_est_lbl.config(text='Lift SG = {:6.1f} ue \n Drag SG = {:6.1f} ue'.format(-est_liftdrag[-1,0], -est_liftdrag[-1,1])) #Predictions are shape:(pred_count, sensor_count)
    except:
      pass
    try:
      read_data = self.data_queue.get_nowait() #THIS DOESN'T REMOVE FROM DATA QUEUE
      self.data_queue.put_nowait(read_data)
      truth_liftdrag = read_data[14:16]
      self.liftdrag_truth_lbl.config(text='Lift SG = {:6.1f} ue \n Drag SG = {:6.1f} ue'.format(-truth_liftdrag[0,-1], -truth_liftdrag[1,-1])) #Rawdata is shape:(sensor_count, data_count)
    except:
      pass     
    self.parent.after(int(self.plot_refresh_rate*1000), self.update_liftdrag_lbls)

  def draw_liftdrag_plots(self, xs, ys, visible_duration, params, pred_sample_size, stall_model_path, liftdrag_model_path, plot_compensated_strains, onlyplot, row, col, label):
    estimate = True if label == "(Predicted)" else False
    lblshift = -2 if estimate else +2
    queue = self.liftdragest_queue if estimate else self.data_queue

    plot = plot_commSGs_westimates_helper.PlotData(pred_sample_size, stall_model_path, liftdrag_model_path, singleplot=True, realtime=True)
    plot.init_realtime_params(visible_duration, self.downsample_mult, params, self.plot_refresh_rate)
    plot.plot_liftdrag(xs, ys)
    plot.term_common_params()
    plot_lbl = Label(self.parent, text='Lift/Drag\n {}'.format(label), font=("Helvetica", 18), justify='center')
    plot_lbl.grid(row=row, column=col+lblshift, rowspan=1, columnspan=1)
    canvas = FigureCanvasTkAgg(plot.fig, master=self.parent)
    canvas.get_tk_widget().grid(row=row, column=col, rowspan=1, columnspan=1)
    truth_ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(ys,queue,plot_compensated_strains,onlyplot,estimate), interval=self.plot_refresh_rate*1000, blit=True) #THIS DOESN'T REMOVE FROM DATA QUEUE
    self.update()
  
  def print_queuelens(self):
    while True:
      print ("Data queue: {}".format(self.data_queue.qsize()))
      print ("Lift/drag queue: {}".format(self.liftdragest_queue.qsize()))
      print ("Stall queue: {}".format(self.stallest_queue.qsize()))
      print ("Shape queue: {}".format(self.shape_queue.qsize()))
      time.sleep (1)

if __name__ == "__main__":
  #Define parameters
  params = dict()
  params["sample_rate"] = 7000 #This will not be the actual sampling rate. NI uses sampling rate of something around for this input 1724.
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.1 #seconds
  keras_samplesize=233 #This is also used for pred_freq. Bad naming here.
  downsample_mult = keras_samplesize #For this app these two are equal to have equal number of lift/drag values. 
  plot_compensated_strains = False
  onlyplot = False
  
  title_labels = ("Measurements", "i-FlyNet Estimates")

  xs = np.linspace (0, visible_duration, int(visible_duration*params["sample_rate"]/downsample_mult))
  ys_truth = np.zeros((2,int(visible_duration*params["sample_rate"]/downsample_mult))) #Here ys only has commlift & commdrag
  ys_preds = np.zeros((2,int(visible_duration*params["sample_rate"]/downsample_mult))) #Here ys only has commlift & commdrag
  video_names = ("AoA view", "Outer MFC view")
  camnums = (1,0)

  stall_model_filename = 'stall_train993_val_988' #stall_train993_val_988
  liftdrag_model_filename = 'lift_train_loss0461'
  stall_model_path = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Kerasfiles/{}.hdf5'.format(stall_model_filename)
  liftdrag_model_path = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Kerasfiles/{}.hdf5'.format(liftdrag_model_filename)

  root = Tk()
  root.title ("Real-time Ground Truth and i-FlyNet Estimation")
  # root.geometry("1000x1200")

  app = GroundTruthAndiFlyNetEstimatesWindow(root, plot_refresh_rate, downsample_mult)
  app.getSGoffsets(params)
  app.init_UI(title_labels)
  app.draw_videos(video_names, camnums)
  app.captureData(params)
  app.initialize_estimates(keras_samplesize, stall_model_path, liftdrag_model_path, plot_refresh_rate)
  
  app.draw_stall_lbl()
  app.draw_liftdrag_lbl()
  app.update_stallest_lbls()
  app.update_liftdrag_lbls()

  app.draw_liftdrag_plots(xs, ys_truth, visible_duration, params, downsample_mult, stall_model_path, liftdrag_model_path, plot_compensated_strains, onlyplot, 2, 0, "(Measured)")
  app.draw_liftdrag_plots(xs, ys_preds, visible_duration, params, downsample_mult, stall_model_path, liftdrag_model_path, plot_compensated_strains, onlyplot, 2, 5, "(Predicted)")
  app.draw_MFCshapes()

  root.mainloop()