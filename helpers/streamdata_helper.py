import numpy as np
import time
from tkinter import Tk, Frame, Canvas, Label
from multiprocessing import Queue, Process
from threading import Thread
from matplotlib.animation import FuncAnimation


class StreamData:
  def __init__ (self, GUIapp, params, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate):
    self.GUIapp = GUIapp
    self.params = params
    self.use_compensated_strains = use_compensated_strains
    self.downsample_mult = downsample_mult
    self.visible_duration = visible_duration
    self.plot_refresh_rate = plot_refresh_rate


class StreamRealTime (StreamData):
  def __init__ (self, GUIapp, params, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate):
    super(StreamRealTime, self).__init__(GUIapp, params, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate)

  def init_and_stream_sensordata(self, mfcplot_exists):
    xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
    ys = np.zeros((18,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag
    self.GUIapp.draw_sensordata_plot(xs, ys, self.visible_duration, self.params, self.use_compensated_strains, mfcplot_exists)

  def init_and_stream_measurements(self):
    xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
    ys = np.zeros((2,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag
    self.GUIapp.update_liftdrag_lbls(predictions=False)
    self.GUIapp.draw_liftdrag_plots(xs, ys, self.visible_duration, self.params, self.downsample_mult, self.use_compensated_strains, False)

  def init_and_stream_estimates(self, models=None):
    if models != None: #Making keras estimates
      xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
      ys_preds = np.zeros((2,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag 
      self.GUIapp.initialize_estimates(self.downsample_mult, models) #Making estimations removes from data_queue
      self.GUIapp.update_stallest_lbls()
      self.GUIapp.update_liftdrag_lbls(predictions=True)
      self.GUIapp.draw_liftdrag_plots(xs, ys_preds, self.visible_duration, self.params, self.downsample_mult, self.use_compensated_strains, True)
    self.GUIapp.draw_MFCshapes(plot_type='contour', blit=True) #Possible plot types are contour or surface
  
  def refresh_queues(self):
    all_queues_list = [self.GUIapp.data_queue, self.GUIapp.stallest_queue, self.GUIapp.liftdragest_queue, self.GUIapp.shape_queue]
    while True:
      for queue in all_queues_list:
        while queue.qsize() > 1: #To keep up with the delay.
            try:
              _ = queue.get_nowait()
            except:
              pass
      time.sleep(self.plot_refresh_rate/3)
      if self.visible_duration == 0:
        break
      


class StreamOffline (StreamData):
  def __init__ (self, GUIapp, params, streamhold_queue, filespath, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate):
    super(StreamOffline, self).__init__(GUIapp, params, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate)
    self.streamhold_queue = streamhold_queue
    self.filespath = filespath

  def initialize_video(self, video_labels, camnums):
    video1, video2 = self.GUIapp.draw_videos(video_labels, camnums, realtime=False, videopath=self.filespath)
    self.videos = [video1, video2]
    videostream_thr_0 = Thread(target=self.stream_video, args=(0,))
    videostream_thr_1 = Thread(target=self.stream_video, args=(1,))
    videostream_thr_0.start()
    videostream_thr_1.start()
    if len(camnums) > 2: #Also airspeed video
      airspeed = self.GUIapp.draw_airspeed(video_labels, camnums, realtime=False, videopath=self.filespath)
      self.videos.append (airspeed)
      videostream_thr_2 = Thread(target=self.stream_video, args=(2,))
      videostream_thr_2.start()
    print ("Initialized videos")
  
  def stream_video(self, videoid):
    while True: #Wait
      if not self.streamhold_queue.empty():
        print ("Started streaming video {}".format(videoid))
        time_delay = 0.6 #This time delay is here because it takes a bit that video actually starts after stream_images command. Increasing this makes video go earlier than plots.
        self.start_time = time.time() + time_delay
        self.videos[videoid].stream_images(self.start_time - time_delay, 1/30)
        break
      else:
        pass
    
  
  def initialize_sensordata(self, mfcplot_exists):
    xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
    ys = np.zeros((16,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult)))
    signalplot = self.GUIapp.draw_sensordata_plot(xs, ys, self.visible_duration, self.params, self.use_compensated_strains, mfcplot_exists)
    signalstream_thr = Thread(target=self.stream_sensordata, args=(signalplot, self.GUIapp.data_list, ys))
    signalstream_thr.start()
    print ("Initialized sensor signals")

  def stream_sensordata(self, signalplot, data_list, ys):
    while True: #Wait
      if not self.streamhold_queue.empty():
        time.sleep(0.02)
        print ("Started streaming sensor signals")
        _ = FuncAnimation(signalplot.fig, signalplot.plot_live, fargs=(ys, data_list, self.use_compensated_strains, self.start_time), interval=self.plot_refresh_rate*1000, blit=True) #DOESN'T REMOVE FROM data_queue 
        self.GUIapp.update()
        break
      else:
        pass


  def initialize_measurements(self):
    xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
    ys = np.zeros((2,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag
    measplot = self.GUIapp.draw_liftdrag_plots(xs, ys, self.visible_duration, self.params, self.downsample_mult, self.use_compensated_strains, False)
    measstream_thr = Thread(target=self.stream_measurements, args=(measplot, self.GUIapp.data_list, ys))
    measstream_thr.start()
    print ("Initialized measurements")
        
  def stream_measurements(self, measplot, data_list, ys): 
    while True: #Wait
      time.sleep(0.1)
      if not self.streamhold_queue.empty():
        print ("Started streaming measurements")
        self.GUIapp.update_liftdrag_lbls(predictions=False, start_time=self.start_time)
        _ = FuncAnimation(measplot.fig, measplot.plot_live, fargs=(ys, data_list, self.use_compensated_strains, False, self.start_time), interval=self.plot_refresh_rate*1000, blit=True) #DOESN'T REMOVE FROM data_queue 
        self.GUIapp.update()
        break
      else:
        pass


  def initialize_estimates(self, stallest, liftdragest, mfcest, stateest, plots, wing_cartoon):
    xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
    ys_preds = np.zeros((2,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag 
    if liftdragest:
      if plots:
        self.liftdrag_predsplot = self.GUIapp.draw_liftdrag_plots(xs, ys_preds, self.visible_duration, self.params, self.downsample_mult, self.use_compensated_strains, True)
    if mfcest:
      if plots:
        self.MFCplot = self.GUIapp.draw_MFCshapes()    
    eststream_thr = Thread(target=self.stream_estimates, args=(self.GUIapp.liftdragest_list, self.GUIapp.shape_list, ys_preds, stallest, liftdragest, mfcest, stateest, plots, wing_cartoon))
    eststream_thr.start()

  def stream_estimates(self, liftdragest_list, shape_list, ys_preds, stallest, liftdragest, mfcest, stateest, plots, wing_cartoon):
    plot_type = 'contour'
    blit = True
    while True: #Wait
      if not self.streamhold_queue.empty():
        print ("Started streaming estimates")
        if stallest:
          time.sleep(0.05)
          self.GUIapp.update_stallest_lbls(start_time=self.start_time)
        if stateest:
          time.sleep(0.05)
          self.GUIapp.update_stateest_lbls(start_time=self.start_time)
        if liftdragest:
          self.GUIapp.update_liftdrag_lbls(predictions=True, start_time=self.start_time)
          if plots:
            _ = FuncAnimation(self.liftdrag_predsplot.fig, self.liftdrag_predsplot.plot_live, fargs=(ys_preds, liftdragest_list, self.use_compensated_strains, True, self.start_time), interval=self.plot_refresh_rate*1000, blit=True)
            time.sleep(0.3)
        if mfcest:
          self.GUIapp.update_mfc_lbls(start_time=self.start_time)
          time.sleep(0.05)
          if plots:
            _ = FuncAnimation(self.MFCplot.fig, self.MFCplot.plot_live, fargs=(shape_list, plot_type, blit, self.start_time), interval=self.plot_refresh_rate*1000, blit=blit)
            time.sleep(0.25)
        if wing_cartoon:
          if stateest:
            self.GUIapp.update_wing_cartoon(old_aoa=0, start_time=self.start_time)
            time.sleep(0.1)
        self.GUIapp.update()
        break
      else:
        pass


  def initialize_plots_wcomparison(self, plot_airspeed, plot_aoa, plot_lift, plot_drag):
    self.airspeed_plot = None
    self.aoa_plot = None
    self.lift_plot = None
    self.drag_plot = None

    if plot_airspeed:
      self.airspeed_plot = self.GUIapp.draw_airspeed_plot_wcomparison(self.visible_duration, self.params, self.downsample_mult)
    if plot_aoa:
      self.aoa_plot = self.GUIapp.draw_aoa_plot_wcomparison(self.visible_duration, self.params, self.downsample_mult)
    if plot_lift:
      self.lift_plot = self.GUIapp.draw_lift_plot_wcomparison(self.visible_duration, self.params, self.downsample_mult)
    if plot_drag:
      self.drag_plot = self.GUIapp.draw_drag_plot_wcomparison(self.visible_duration, self.params, self.downsample_mult)
    
    plots_wcomparison_thr = Thread(target=self.stream_plots_wcomparison)
    plots_wcomparison_thr.start()
    print ("Initialized plotting w_comparisons")

  def stream_plots_wcomparison(self):
    while True: #Wait
      if not self.streamhold_queue.empty():
        print ("Started streaming plotting w_comparisons")
        if self.airspeed_plot is not None:
          time.sleep(0.05)
          _ = FuncAnimation(self.airspeed_plot.fig, self.airspeed_plot.plot_airspeed_live, fargs=(self.GUIapp.meas_airspeed_list, self.GUIapp.stateest_list, self.start_time), interval=self.plot_refresh_rate*1000, blit=True)
        if self.aoa_plot is not None:
          time.sleep(0.05)
          _ = FuncAnimation(self.aoa_plot.fig, self.aoa_plot.plot_aoa_live, fargs=(self.GUIapp.meas_aoa_list, self.GUIapp.stateest_list, self.start_time), interval=self.plot_refresh_rate*1000, blit=True)
        if self.lift_plot is not None:
          time.sleep(0.05)
          _ = FuncAnimation(self.lift_plot.fig, self.lift_plot.plot_lift_live, fargs=(self.GUIapp.data_list, self.GUIapp.liftdragest_list, self.use_compensated_strains, self.start_time), interval=self.plot_refresh_rate*1000, blit=True)
        if self.drag_plot is not None:
          time.sleep(0.05)
          _ = FuncAnimation(self.drag_plot.fig, self.drag_plot.plot_drag_live, fargs=(self.GUIapp.data_list, self.GUIapp.liftdragest_list, self.use_compensated_strains, self.start_time), interval=self.plot_refresh_rate*1000, blit=True)
        self.GUIapp.update()
        break
      else:
        pass