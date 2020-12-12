import time
import sys
import os
import numpy as np
from tkinter import *
from tkinter import Tk, Frame, Button, Label, Canvas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from threading import Thread
from multiprocessing import Process, Queue

sys.path.append(os.path.abspath('./fbf-DAQ'))
sys.path.append(os.path.abspath('./helpers'))
import daq_captureANDstreamvideo_helper
import plot_sensordata_helper
import plot_commSGs_westimates_helper
import proc_keras_estimates_helper
import proc_MFCshape_helper
import plot_MFC_helper


#Plotting in TK class
class GroundTruthAndiFlyNetEstimatesWindow(Frame):
  def __init__(self, parent, plot_refresh_rate, downsample_mult, offline=False):
    Frame.__init__(self,parent)
    self.parent = parent
    self.stall_cond = "No"
    self.truth_lift_val = 0
    self.truth_drag_val = 0
    self.est_lift_val = 0
    self.est_drag_val = 0
    self.plot_refresh_rate = plot_refresh_rate
    self.downsample_mult = downsample_mult
    self.offline = offline


  def getSGoffsets (self, params):
    #Capture SG offsets:
    import daq_captureSGoffsets_helper
    q1 = Queue()
    p1 = Thread(target = daq_captureSGoffsets_helper.send_SG_offsets, args=(params["sample_rate"], int(params["sample_rate"]), q1))
    p1.start()
    self.SGoffsets = q1.get()
    p1.join()

  def captureData (self, params, saveflag_queue=None, save_duration=None, saver=None):
    # Run capture data in background
    import daq_capturedata_helper
    if saver == None:
      self.get_data_proc = Process(target = daq_capturedata_helper.send_data, args=(self.SGoffsets, params["sample_rate"], int(params["sample_rate"]*self.plot_refresh_rate), "continuous", self.data_queue))
    else:
      self.get_data_proc = Process(target = daq_capturedata_helper.send_data, args=(self.SGoffsets, params["sample_rate"], int(params["sample_rate"]*self.plot_refresh_rate), "continuous", self.data_queue, saveflag_queue, save_duration, saver))
    self.get_data_proc.start()

  
  def init_UI (self, labels):
    self.lbl1 = Label(self.parent, text=labels[0], font=("Helvetica", 21, 'bold', 'underline'), justify='center')
    self.lbl2 = Label(self.parent, text=labels[1], font=("Helvetica", 21, 'bold', 'underline'), justify='center')

  def initialize_queues_or_lists (self):
    if not self.offline:
      self.data_queue = Queue()
      self.stallest_queue = Queue()
      self.liftdragest_queue = Queue()
      self.shape_queue = Queue()
    else:
      self.data_list = list()
      self.stallest_list = list()
      self.liftdragest_list = list()
      self.shape_list = list()

  def initialize_estimates (self, pred_freq, models):
    self.estimates = proc_keras_estimates_helper.iFlyNetEstimates(pred_freq, models)
    t_estimations = Thread(target = self.update_estimations)
    t_estimations.start()

  def draw_stall_lbl (self):
    self.stall_lbl = Label(self.parent, text='Stall?', font=("Helvetica", 18), justify='center')
    self.stall_cond_lbl = Label(self.parent, text=self.stall_cond, font=("Arial", 26), justify='center')

  def draw_liftdrag_lbl (self):
    self.liftdrag_truth_lbl = Label(self.parent, text='Lift SG = {} ue \n Drag SG = {} ue'.format(self.truth_lift_val, self.truth_drag_val), font=("Helvetica", 16), width=20)
    self.liftdrag_est_lbl = Label(self.parent, text='Lift SG = {} ue \n Drag SG = {} ue'.format(self.est_lift_val, self.est_drag_val), font=("Helvetica", 16), width=20)


  def update_estimations(self):
    while True:
      try:
        read_data = self.data_queue.get_nowait()
        self.data_queue.put_nowait(read_data)
        useful_data_start, useful_data_end = 0, int(read_data.shape[1]/self.downsample_mult)*self.downsample_mult
        stall_predictors = np.concatenate ((read_data[0:6], read_data[14:16]), axis=0) #Use PZTs+CommSGs for stall predictions
        self.stallest_queue.put_nowait (np.any(self.estimates.estimate_stall(stall_predictors[:,useful_data_start:useful_data_end])))
        liftdrag_predictors = read_data[0:6] #Use onlyPZTs for liftdrag predictions
        self.liftdragest_queue.put_nowait (self.estimates.estimate_liftdrag(liftdrag_predictors[:,useful_data_start:useful_data_end]))
      except:
        pass
      time.sleep(self.plot_refresh_rate)

  def update_stallest_lbls (self, start_time=None):
    try:
      if not self.offline:
        stall_cond = self.stallest_queue.get_nowait()
      else:
        t0 = time.time()
        cur_frame = int((t0-start_time)/self.plot_refresh_rate)
        stall_cond = self.stallest_list[cur_frame]
      stalltext = "Yes" if stall_cond else "No"
      self.stall_cond_lbl.config(text=stalltext)
    except:
      pass
    self.parent.after(int(self.plot_refresh_rate*1000), self.update_stallest_lbls, start_time)

  def update_liftdrag_lbls (self, predictions, start_time=None):
    if predictions: #PREDICTED LIFT DRAG
      try:
        if not self.offline:
          est_liftdrag = self.liftdragest_queue.get_nowait()
          self.liftdragest_queue.put_nowait(est_liftdrag)
        else:
          t0 = time.time()
          cur_frame = int((t0-start_time)/self.plot_refresh_rate)
          est_liftdrag = self.liftdragest_list[cur_frame]
        self.liftdrag_est_lbl.config(text='Lift SG = {:6.1f} ue \n Drag SG = {:6.1f} ue'.format(-est_liftdrag[-1,0], -est_liftdrag[-1,1])) #Predictions are shape:(pred_count, sensor_count)
      except:
        pass

    else: #TRUTH LIFT DRAG
      try:
        if not self.offline:
          read_data = self.data_queue.get_nowait()
          self.data_queue.put_nowait(read_data)
        else:
          t0 = time.time()
          cur_frame = int((t0-start_time)/self.plot_refresh_rate)
          read_data = self.data_list[cur_frame]
        truth_liftdrag = read_data[14:16]
        self.liftdrag_truth_lbl.config(text='Lift SG = {:6.1f} ue \n Drag SG = {:6.1f} ue'.format(-truth_liftdrag[0,-1], -truth_liftdrag[1,-1])) #Rawdata is shape:(sensor_count, data_count)
      except:
        pass     
    
    self.parent.after(int(self.plot_refresh_rate*1000), self.update_liftdrag_lbls, predictions, start_time)



  def draw_videos(self, video_names, camnums, realtime=True, videopath=None):
      if not realtime:
        self.video1 = daq_captureANDstreamvideo_helper.DrawTKOfflineVideo(self.parent, video_names[0], camnums[0], videopath)
        self.video2 = daq_captureANDstreamvideo_helper.DrawTKOfflineVideo(self.parent, video_names[1], camnums[1], videopath)
        return (self.video1, self.video2)
      else:  
        self.video1 = daq_captureANDstreamvideo_helper.DrawTKVideoCapture(self.parent, video_names[0], camnums[0])
        self.video2 = daq_captureANDstreamvideo_helper.DrawTKVideoCapture(self.parent, video_names[1], camnums[1])
        self.video1.multithreaded_capture(init_call=True) #Use for multi-threaded executions
        self.video2.multithreaded_capture(init_call=True) #Use for multi-threaded executions
        # video1.update() #Use for single threaded executions
        # video2.update() #Use for single threaded executions


  def draw_sensordata_plot(self, xs, ys, visible_duration, params, plot_compensated_strains, mfcplot_exists):
    plot = plot_sensordata_helper.PlotSensorData(self.downsample_mult, singleplot=True, ongui=True, offline=self.offline, reftemp=self.reftemps)
    self.sensordata_plot = plot
    plot.init_realtime_params(visible_duration, params, self.plot_refresh_rate)
    plot.plot_raw_lines(xs, ys)
    plot.term_common_params(mfcplot_exists)

    self.sensordata_plot_cvs = FigureCanvasTkAgg(plot.fig, master=self.parent)
    
    if not self.offline:
      _ = FuncAnimation(plot.fig, plot.plot_live, fargs=(ys, self.data_queue, plot_compensated_strains, None, None), interval=self.plot_refresh_rate*1000, blit=True)
      self.update()
    else:
      return plot
    


  def draw_liftdrag_plots(self, xs, ys, visible_duration, params, pred_sample_size, plot_compensated_strains, estimate):
    label = "(Predicted)" if estimate else "(Measured)"
    if not self.offline:
      queue = self.liftdragest_queue if estimate else self.data_queue

    plot = plot_commSGs_westimates_helper.PlotData(pred_sample_size, singleplot=True, ongui=True, offline=self.offline)
    plot.init_realtime_params(visible_duration, self.downsample_mult, params, self.plot_refresh_rate)
    plot.plot_liftdrag(xs, ys)
    plot.term_common_params()
    if not estimate:
      self.truth_liftdrag_plot_lbl = Label(self.parent, text='Lift/Drag\n {}'.format(label), font=("Helvetica", 18), justify='center')
      self.truth_liftdrag_plot_cvs = FigureCanvasTkAgg(plot.fig, master=self.parent)
    else:
      self.est_liftdrag_plot_lbl = Label(self.parent, text='Lift/Drag\n {}'.format(label), font=("Helvetica", 18), justify='center')
      self.est_liftdrag_plot_cvs = FigureCanvasTkAgg(plot.fig, master=self.parent)
    
    if not self.offline:
      _ = FuncAnimation(plot.fig, plot.plot_live, fargs=(ys, queue, plot_compensated_strains, estimate, None), interval=self.plot_refresh_rate*1000, blit=True)
    else:
      return plot
    self.update()


  def draw_MFCshapes(self, plot_type='contour', blit=True):    
    mfc_shape = proc_MFCshape_helper.CalcMFCShape(self.plot_refresh_rate)
    if not self.offline:
      self.draw_MFC_proc = Process(target = mfc_shape.supply_data, args=(self.shape_queue, self.data_queue, False))
      self.draw_MFC_proc.start()

    plot = plot_MFC_helper.PlotMFCShape(self.plot_refresh_rate, mfc_shape.XVAL, mfc_shape.YVAL, offline=self.offline)
    plot.plot_2D_contour()
    self.mfc_lbl = Label(self.parent, text="Morphing\nsection shape", font=("Helvetica", 18), justify='center')
    self.mfc_canvas = FigureCanvasTkAgg(plot.fig, master=self.parent)
    
    if not self.offline:
      _ = FuncAnimation(plot.fig, plot.plot_live, fargs=(self.shape_queue, plot_type, blit, None), interval=self.plot_refresh_rate*1000, blit=blit)
    else:
      return plot
    self.update()


  def place_on_grid(self, raw_signal, keras_preds, MFC_preds):
    if raw_signal==True and keras_preds==False and MFC_preds==False: #offline_signal_gui and realtime_signal_gui
      self.video1.videolbl.grid(row=0, column=1, rowspan=1, columnspan=1, sticky=S)
      self.video1.videocvs.grid(row=1, column=0, rowspan=2, columnspan=3, sticky=N)
      self.video2.videolbl.grid(row=3, column=1, rowspan=1, columnspan=1, sticky=S)
      self.video2.videocvs.grid(row=4, column=0, rowspan=2, columnspan=3, sticky=N)
      
      self.sensordata_plot_cvs.get_tk_widget().grid(row=2, column=3, rowspan=3, columnspan=3)

    if raw_signal==True and keras_preds==False and MFC_preds==True: #offline_signal_shape_gui and realtime_signal_shape_gui    
      self.video1.videolbl.grid(row=5, column=0, rowspan=1, columnspan=3, sticky=S)
      self.video1.videocvs.grid(row=6, column=0, rowspan=1, columnspan=3, sticky=N)
      self.video2.videolbl.grid(row=12, column=0, rowspan=1, columnspan=3, pady=5, sticky=S)
      self.video2.videocvs.grid(row=13, column=0, rowspan=1, columnspan=3, sticky=N)
      
      self.sensordata_plot_cvs.get_tk_widget().grid(row=1, column=3, rowspan=11, columnspan=3)
      self.mfc_lbl.grid(row=12, column=4, rowspan=1, columnspan=1, sticky=S)
      self.mfc_canvas.get_tk_widget().grid(row=13, column=3, rowspan=1, columnspan=3, sticky=N)


    if raw_signal==False and keras_preds==True and MFC_preds==True: #offline_all_gui and realtime_all_gui
      self.lbl1.grid(row=0, column=0, rowspan=1, columnspan=2, sticky=S)
      self.lbl2.grid(row=0, column=4, rowspan=1, columnspan=2, sticky=S)

      self.video1.videolbl.grid(row=1, column=2, rowspan=1, columnspan=1)
      self.video1.videocvs.grid(row=1, column=0, rowspan=1, columnspan=2)
      self.video2.videolbl.grid(row=3, column=2, rowspan=1, columnspan=1)
      self.video2.videocvs.grid(row=3, column=0, rowspan=1, columnspan=2)

      self.stall_lbl.grid(row=1, column=3, rowspan=1, columnspan=1)
      self.stall_cond_lbl.grid(row=1, column=4, rowspan=1, columnspan=1, sticky=W)
      self.liftdrag_truth_lbl.grid(row=2, column=1, rowspan=1, columnspan=1, sticky=W)
      self.liftdrag_est_lbl.grid(row=2, column=4, rowspan=1, columnspan=1, sticky=W)  
      self.truth_liftdrag_plot_lbl.grid(row=2, column=2, rowspan=1, columnspan=1)
      self.truth_liftdrag_plot_cvs.get_tk_widget().grid(row=2, column=0, rowspan=1, columnspan=1)
      self.est_liftdrag_plot_lbl.grid(row=2, column=2, rowspan=1, columnspan=1)
      self.est_liftdrag_plot_cvs.get_tk_widget().grid(row=2, column=5, rowspan=1, columnspan=1)
      
      self.mfc_lbl.grid(row=3, column=3, rowspan=1, columnspan=1, padx=65)
      self.mfc_canvas.get_tk_widget().grid(row=3, column=4, rowspan=1, columnspan=2, sticky=W)
    
    self.update()


  def print_queuelens(self):
    while True:
      print ("Data queue: {}".format(self.data_queue.qsize()))
      print ("Lift/drag queue: {}".format(self.liftdragest_queue.qsize()))
      print ("Stall queue: {}".format(self.stallest_queue.qsize()))
      print ("Shape queue: {}".format(self.shape_queue.qsize()))
      time.sleep (1)