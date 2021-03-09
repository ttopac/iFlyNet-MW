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
import plot_metrics_wcomparison


#Plotting in TK class
class GroundTruthAndiFlyNetEstimatesWindow(Frame):
  def __init__(self, parent, plot_refresh_rate, downsample_mult, offline=False):
    Frame.__init__(self,parent)
    self.parent = parent
    self.stall_cond = "No"
    self.est_airspeed = 0
    self.est_aoa = 0
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
    self.lbls = list()
    for i in range(len(labels)):
      self.lbls.append(Label(self.parent, text=labels[i], font=("Helvetica", 21, 'bold', 'underline'), justify='center'))
    

  def initialize_queues_or_lists (self):
    if not self.offline:
      self.data_queue = Queue()
      self.stallest_queue = Queue()
      self.stateest_queue = Queue()
      self.liftdragest_queue = Queue()
      self.shape_queue = Queue()
      self.meas_airspeed_queue = Queue()
      self.meas_aoa_queue = Queue()
    else:
      self.data_list = list()
      self.stallest_list = list()
      self.stateest_list = list()
      self.liftdragest_list = list()
      self.shape_list = list()
      self.meas_airspeed_list = list()
      self.meas_aoa_list = list()

  def initialize_estimates (self, pred_freq, models):
    self.estimates = proc_keras_estimates_helper.iFlyNetEstimates(pred_freq, models)
    # t_estimations = Thread(target = self.update_estimations)
    # t_estimations.start()

  def draw_stall_lbl (self):
    self.stall_lbl = Label(self.parent, text='Stall?', font=("Helvetica", 18), justify='center')
    self.stall_cond_lbl = Label(self.parent, text=self.stall_cond, font=("Arial", 26), justify='center')

  def draw_state_lbl (self):
    self.state_lbl = Label(self.parent, text='Flight state', font=("Helvetica", 18), justify='center')
    self.state_est_lbl = Label(self.parent, text="Airspeed = {} m/s \n AoA = {} deg".format(self.est_airspeed, self.est_aoa), font=("Arial", 26), justify='center')

  def draw_liftdrag_lbl (self):
    self.liftdrag_truth_lbl = Label(self.parent, text='Lift SG = {} ue \n Drag SG = {} ue'.format(self.truth_lift_val, self.truth_drag_val), font=("Helvetica", 16), width=20)
    self.liftdrag_est_lbl = Label(self.parent, text='Lift SG = {} ue \n Drag SG = {} ue'.format(self.est_lift_val, self.est_drag_val), font=("Helvetica", 16), width=20)

  def draw_airspeed_lbl (self):
    self.airspeedlbl = Label(self.parent, text='Airspeed\n(WT data)', font=("Helvetica", 18), justify='center')

  def draw_cartoon_lbl (self):
    self.cartoon_lbl = Label(self.parent, text='Wing state (i-FlyNet)', font=("Helvetica", 21, 'bold', 'underline'), justify='center')


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

  def update_stateest_lbls (self, start_time=None):
    try:
      if not self.offline:
        state_est = self.stateest_queue.get_nowait()
      else:
        t0 = time.time()
        cur_frame = int((t0-start_time)/self.plot_refresh_rate)
        state_est = self.stateest_list[cur_frame]
      self.state_est_lbl.config(text="Airspeed = {} m/s \n AoA = {} deg".format(int(state_est[0]), int(state_est[1]))) #Predictions are shape:(pred_count, output_count)
    except:
      pass
    self.parent.after(int(self.plot_refresh_rate*1000), self.update_stateest_lbls, start_time)

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
        self.liftdrag_est_lbl.config(text='Lift SG = {:6.1f} ue \n Drag SG = {:6.1f} ue'.format(-est_liftdrag[-1,0], -est_liftdrag[-1,1])) #Predictions are shape:(pred_count, output_count)
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
    self.videos = list()
    if not realtime:
      for i in range(len(camnums)):
        self.videos.append (daq_captureANDstreamvideo_helper.DrawTKOfflineVideo(self.parent, video_names[i], camnums[i], videopath))
      return (self.videos)
    else:
      for i in range(len(camnums)):
        self.videos.append (daq_captureANDstreamvideo_helper.DrawTKVideoCapture(self.parent, video_names[i], camnums[i]))
      for i in range(len(camnums)):
        self.videos[i].multithreaded_capture(init_call=True) #Use for multi-threaded executions
        self.videos[i].update() #Use for single threaded executions
  
  def draw_airspeed(self, video_names, camnums, realtime, videopath):
    if not realtime:
      self.airspeed_video = daq_captureANDstreamvideo_helper.DrawTKOfflineVideo(self.parent, video_names[2], camnums[2], videopath)
      return self.airspeed_video
    else: 
      raise NotImplementedError

  def draw_sensordata_plot(self, xs, ys, visible_duration, params, plot_compensated_strains, mfcplot_exists):
    if plot_compensated_strains:
      reftemps = self.reftemps
    else:
      reftemps = None
    plot = plot_sensordata_helper.PlotSensorData(self.downsample_mult, singleplot=True, ongui=True, offline=self.offline, reftemp=reftemps)
    plot.init_realtime_params(visible_duration, params, self.plot_refresh_rate)
    plot.plot_raw_lines(xs, ys)
    plot.term_common_params(mfcplot_exists)

    self.sensordata_plot = plot
    self.sensordata_plot_cvs = FigureCanvasTkAgg(plot.fig, master=self.parent)
    
    if not self.offline:
      _ = FuncAnimation(plot.fig, plot.plot_live, fargs=(ys, self.data_queue, plot_compensated_strains, None), interval=self.plot_refresh_rate*1000, blit=True)
      print ("Started sensordata plot.")
      self.update()
    else:
      return plot
    
  def draw_liftdrag_plots(self, xs, ys, visible_duration, params, pred_sample_size, plot_compensated_strains, estimate):
    if not self.offline:
      queue = self.liftdragest_queue if estimate else self.data_queue

    plot = plot_commSGs_westimates_helper.PlotData(pred_sample_size, singleplot=True, ongui=True, offline=self.offline)
    plot.init_realtime_params(visible_duration, self.downsample_mult, params, self.plot_refresh_rate)
    plot.plot_liftdrag(xs, ys)
    plot.term_common_params()
    if not estimate:
      self.truth_liftdrag_plot_lbl = Label(self.parent, text='Lift/Drag', font=("Helvetica", 18), justify='center')
      self.truth_liftdrag_plot_cvs = FigureCanvasTkAgg(plot.fig, master=self.parent)
    else:
      self.est_liftdrag_plot_lbl = Label(self.parent, text='Lift/Drag', font=("Helvetica", 18), justify='center')
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




  def draw_cartoon_cvs (self):
    self.cartoon_cvs = Canvas(self.parent, width=640, height=360)
    self.cartoon_cvs.create_rectangle(3,3,640,360, width=2)




  def draw_airspeed_plot_wcomparison(self, xs, ys, visible_duration, params, pred_sample_size):
    if not self.offline:
      raise NotImplementedError

    airspeed_plot = plot_metrics_wcomparison.AirspeedPlot(pred_sample_size, ongui=True, offline=self.offline)
    airspeed_plot.init_realtime_params(visible_duration, self.downsample_mult, params, self.plot_refresh_rate)
    airspeed_plot.init_common_params("V (m/s)")
    airspeed_plot.plot_airspeed_wcomparison(xs, ys)
    airspeed_plot.term_common_params()

    self.airspeed_plot_wcomparison_lbl = Label(self.parent, text='Airspeed', font=("Helvetica", 18), justify='center')
    self.airspeed_plot_wcomparison_cvs = FigureCanvasTkAgg(airspeed_plot.fig, master=self.parent)
    return airspeed_plot

  def draw_aoa_plot_wcomparison(self, xs, ys, visible_duration, params, pred_sample_size):
    if not self.offline:
      raise NotImplementedError

    aoa_plot = plot_metrics_wcomparison.AoaPlot(pred_sample_size, ongui=True, offline=self.offline)
    aoa_plot.init_realtime_params(visible_duration, self.downsample_mult, params, self.plot_refresh_rate)
    aoa_plot.init_common_params("AoA (deg)")
    aoa_plot.plot_aoa_wcomparison(xs, ys)
    aoa_plot.term_common_params()

    self.aoa_plot_wcomparison_lbl = Label(self.parent, text='Angle of Attack', font=("Helvetica", 18), justify='center')
    self.aoa_plot_wcomparison_cvs = FigureCanvasTkAgg(aoa_plot.fig, master=self.parent)
    return aoa_plot

  def draw_lift_plot_wcomparison(self, xs, ys, visible_duration, params, pred_sample_size):
    if not self.offline:
      raise NotImplementedError

    lift_plot = plot_metrics_wcomparison.LiftPlot(pred_sample_size, ongui=True, offline=self.offline)
    lift_plot.init_realtime_params(visible_duration, self.downsample_mult, params, self.plot_refresh_rate)
    lift_plot.init_common_params("Lift")
    lift_plot.plot_lift_wcomparison(xs, ys)
    lift_plot.term_common_params()

    self.lift_plot_wcomparison_lbl = Label(self.parent, text='Lift Force', font=("Helvetica", 18), justify='center')
    self.lift_plot_wcomparison_cvs = FigureCanvasTkAgg(lift_plot.fig, master=self.parent)
    return lift_plot

  def draw_drag_plot_wcomparison(self, xs, ys, visible_duration, params, pred_sample_size):
    if not self.offline:
      raise NotImplementedError

    drag_plot = plot_metrics_wcomparison.DragPlot(pred_sample_size, ongui=True, offline=self.offline)
    drag_plot.init_realtime_params(visible_duration, self.downsample_mult, params, self.plot_refresh_rate)
    drag_plot.init_common_params("Drag")
    drag_plot.plot_drag_wcomparison(xs, ys)
    drag_plot.term_common_params()

    self.drag_plot_wcomparison_lbl = Label(self.parent, text='Drag Force', font=("Helvetica", 18), justify='center')
    self.drag_plot_wcomparison_cvs = FigureCanvasTkAgg(drag_plot.fig, master=self.parent)
    return drag_plot



  def place_on_grid(self, raw_signal, keras_preds, MFC_preds, keras_state_preds=False, cartoon_gui=False):
    
    if cartoon_gui == True: #offline_all_gui_cartoon
      #Top row
      self.videos[0].videocvs.grid(row=2, column=0, rowspan=1, columnspan=4)
      self.videos[0].videolbl.grid(row=1, column=0, rowspan=1, columnspan=4)
      self.cartoon_lbl.grid(row=1, column=4, rowspan=1, columnspan=4)
      self.cartoon_cvs.grid(row=2, column=4, rowspan=1, columnspan=4)

      #Mid. row
      self.lbls[0].grid(row=3, column=3, rowspan=1, columnspan=2, pady=(10,0))
      
      #Bottom row
      self.airspeed_plot_wcomparison_cvs.get_tk_widget().grid(row=4, column=0, rowspan=1, columnspan=2, padx=(10,5))
      self.aoa_plot_wcomparison_cvs.get_tk_widget().grid(row=4, column=2, rowspan=1, columnspan=2, padx=(5,5))
      self.lift_plot_wcomparison_cvs.get_tk_widget().grid(row=4, column=4, rowspan=1, columnspan=2, padx=(5,5))
      self.drag_plot_wcomparison_cvs.get_tk_widget().grid(row=4, column=6, rowspan=1, columnspan=2, padx=(5,10))      
    

    if raw_signal==True and keras_preds==False and MFC_preds==False and keras_state_preds==False: #offline_signal_gui and realtime_signal_gui
      self.videos[0].videolbl.grid(row=0, column=1, rowspan=1, columnspan=1, sticky=S)
      self.videos[0].videocvs.grid(row=1, column=0, rowspan=2, columnspan=3, sticky=N)
      self.videos[1].videolbl.grid(row=3, column=1, rowspan=1, columnspan=1, sticky=S)
      self.videos[1].videocvs.grid(row=4, column=0, rowspan=2, columnspan=3, sticky=N)
      
      self.sensordata_plot_cvs.get_tk_widget().grid(row=2, column=3, rowspan=3, columnspan=3)


    if raw_signal==True and keras_preds==False and MFC_preds==True and keras_state_preds==False: #offline_signal_shape_gui and realtime_signal_shape_gui    
      self.videos[0].videolbl.grid(row=5, column=0, rowspan=1, columnspan=3, sticky=S)
      self.videos[0].videocvs.grid(row=6, column=0, rowspan=1, columnspan=3, sticky=N)
      self.videos[1].videolbl.grid(row=12, column=0, rowspan=1, columnspan=3, pady=5, sticky=S)
      self.videos[1].videocvs.grid(row=13, column=0, rowspan=1, columnspan=3, sticky=N)
      
      self.sensordata_plot_cvs.get_tk_widget().grid(row=1, column=3, rowspan=11, columnspan=3)
      self.mfc_lbl.grid(row=12, column=4, rowspan=1, columnspan=1, sticky=S)
      self.mfc_canvas.get_tk_widget().grid(row=13, column=3, rowspan=1, columnspan=3, sticky=N)


    if raw_signal==False and keras_preds==True and MFC_preds==True and keras_state_preds==False: #offline_all_gui and realtime_all_gui
      self.lbls[0].grid(row=0, column=0, rowspan=1, columnspan=2, sticky=S)
      self.lbls[1].grid(row=0, column=4, rowspan=1, columnspan=2, sticky=S)

      self.videos[0].videolbl.grid(row=1, column=2, rowspan=1, columnspan=1)
      self.videos[0].videocvs.grid(row=1, column=0, rowspan=1, columnspan=2)
      self.videos[1].videolbl.grid(row=3, column=2, rowspan=1, columnspan=1)
      self.videos[1].videocvs.grid(row=3, column=0, rowspan=1, columnspan=2)

      self.stall_lbl.grid(row=1, column=3, rowspan=1, columnspan=1)
      self.stall_cond_lbl.grid(row=1, column=4, rowspan=1, columnspan=1, sticky=W)
      self.liftdrag_truth_lbl.grid(row=2, column=1, rowspan=1, columnspan=1, sticky=W)
      self.liftdrag_est_lbl.grid(row=2, column=4, rowspan=1, columnspan=1, sticky=W)  
      self.truth_liftdrag_plot_lbl.grid(row=2, column=2, rowspan=1, columnspan=1)
      self.truth_liftdrag_plot_cvs.get_tk_widget().grid(row=2, column=0, rowspan=1, columnspan=1)
      self.est_liftdrag_plot_lbl.grid(row=2, column=3, rowspan=1, columnspan=1)
      self.est_liftdrag_plot_cvs.get_tk_widget().grid(row=2, column=5, rowspan=1, columnspan=1)
      
      self.mfc_lbl.grid(row=3, column=3, rowspan=1, columnspan=1, padx=65)
      self.mfc_canvas.get_tk_widget().grid(row=3, column=4, rowspan=1, columnspan=2, sticky=W)

    
    if raw_signal==False and keras_preds==True and MFC_preds==True and keras_state_preds==True: #offline_all_gui_wstate
      self.lbls[0].grid(row=0, column=0, rowspan=1, columnspan=2, sticky=S)
      self.lbls[1].grid(row=0, column=4, rowspan=1, columnspan=2, sticky=S)

      self.videos[0].videolbl.grid(row=1, column=2, rowspan=2, columnspan=1)
      self.videos[0].videocvs.grid(row=1, column=0, rowspan=2, columnspan=2)
      self.videos[1].videolbl.grid(row=4, column=2, rowspan=1, columnspan=1)
      self.videos[1].videocvs.grid(row=4, column=0, rowspan=1, columnspan=2)

      self.stall_lbl.grid(row=1, column=3, rowspan=1, columnspan=1)
      self.stall_cond_lbl.grid(row=1, column=4, rowspan=1, columnspan=1, sticky=W)
      self.state_lbl.grid(row=2, column=3, rowspan=1, columnspan=1)
      self.state_est_lbl.grid(row=2, column=4, rowspan=1, columnspan=2, sticky=W)

      self.liftdrag_truth_lbl.grid(row=3, column=1, rowspan=1, columnspan=1, sticky=W)
      self.liftdrag_est_lbl.grid(row=3, column=4, rowspan=1, columnspan=1, sticky=W)  
      self.truth_liftdrag_plot_lbl.grid(row=3, column=2, rowspan=1, columnspan=1)
      self.truth_liftdrag_plot_cvs.get_tk_widget().grid(row=3, column=0, rowspan=1, columnspan=1)
      self.est_liftdrag_plot_lbl.grid(row=3, column=3, rowspan=1, columnspan=1)
      self.est_liftdrag_plot_cvs.get_tk_widget().grid(row=3, column=5, rowspan=1, columnspan=1)
      
      self.mfc_lbl.grid(row=4, column=3, rowspan=1, columnspan=1, padx=65)
      self.mfc_canvas.get_tk_widget().grid(row=4, column=4, rowspan=1, columnspan=2, sticky=W)
    
    self.update()


  def print_queuelens(self):
    while True:
      print ("Data queue: {}".format(self.data_queue.qsize()))
      print ("Lift/drag queue: {}".format(self.liftdragest_queue.qsize()))
      print ("Stall queue: {}".format(self.stallest_queue.qsize()))
      print ("State queue: {}".format(self.stateest_queue.qsize()))
      print ("Shape queue: {}".format(self.shape_queue.qsize()))
      time.sleep (1)