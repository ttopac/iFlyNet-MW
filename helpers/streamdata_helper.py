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
    ys = np.zeros((16,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag
    self.GUIapp.draw_sensordata_plot(xs, ys, self.visible_duration, self.params, self.use_compensated_strains, mfcplot_exists)

  def init_and_stream_measurements(self):
    xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
    ys_truth = np.zeros((2,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag
    self.GUIapp.update_liftdrag_lbls(predictions=False)
    self.GUIapp.draw_liftdrag_plots(xs, ys_truth, self.visible_duration, self.params, self.downsample_mult, self.use_compensated_strains, False)

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
      


class StreamOffline (StreamData):
  def __init__ (self, GUIapp, params, streamhold_queue, filespath, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate, ref_temp):
    super(StreamOffline, self).__init__(GUIapp, params, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate)
    self.streamhold_queue = streamhold_queue
    self.filespath = filespath
    self.use_compensated_strains = use_compensated_strains
    self.ref_temp = ref_temp

  def initialize_video(self, video_labels, camnums):
    video1, video2 = self.GUIapp.draw_videos(video_labels, camnums, realtime=False, videopath=self.filespath)
    self.videos = [video1, video2]
    videostream_thr_0 = Thread(target=self.stream_video, args=(0,))
    videostream_thr_1 = Thread(target=self.stream_video, args=(1,))
    videostream_thr_0.start()
    videostream_thr_1.start()
    print ("Initialized videos")
  
  def stream_video(self, videoid):
    while True: #Wait
      if not self.streamhold_queue.empty():
        print ("Started streaming video {}".format(videoid))
        self.videos[videoid].stream_images(time.time(), 1/30)
        break
      else:
        pass
    
  
  def initialize_sensordata(self, mfcplot_exists):
    xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
    ys = np.zeros((16,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag
    signalplot = self.GUIapp.draw_sensordata_plot(xs, ys, self.visible_duration, self.params, self.use_compensated_strains, mfcplot_exists)
    signalstream_thr = Thread(target=self.stream_sensordata, args=(signalplot, self.GUIapp.data_list, ys))
    signalstream_thr.start()
    print ("Initialized sensor signals")

  def stream_sensordata(self, signalplot, data_list, ys):
    while True: #Wait
      if not self.streamhold_queue.empty():
        print ("Started streaming sensor signals")
        time.sleep(0.2)
        _ = FuncAnimation(signalplot.fig, signalplot.plot_live, fargs=(ys, data_list, self.use_compensated_strains, self.ref_temp, time.time()), interval=self.plot_refresh_rate*1000, blit=True) #DOESN'T REMOVE FROM data_queue 
        self.GUIapp.update()
        break
      else:
        pass


  def initialize_measurements(self):
    xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
    ys_truth = np.zeros((2,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag
    measplot = self.GUIapp.draw_liftdrag_plots(xs, ys_truth, self.visible_duration, self.params, self.downsample_mult, self.use_compensated_strains, False)
    measstream_thr = Thread(target=self.stream_measurements, args=(measplot, self.GUIapp.data_list, ys_truth))
    measstream_thr.start()
    print ("Initialized measurements")
        
  def stream_measurements(self, measplot, data_list, ys_truth): 
    while True: #Wait
      if not self.streamhold_queue.empty():
        print ("Started streaming measurements")
        self.GUIapp.update_liftdrag_lbls(predictions=False, start_time=time.time())
        time.sleep(0.15)
        _ = FuncAnimation(measplot.fig, measplot.plot_live, fargs=(ys_truth, data_list, self.use_compensated_strains, False, time.time()), interval=self.plot_refresh_rate*1000, blit=True) #DOESN'T REMOVE FROM data_queue 
        self.GUIapp.update()
        break
      else:
        pass


  def initialize_estimates(self, stallest, liftdragest, mfcest):
    xs = np.linspace (0, self.visible_duration, int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))
    ys_preds = np.zeros((2,int(self.visible_duration*self.params["sample_rate"]/self.downsample_mult))) #Here ys only has commlift & commdrag 
    if liftdragest:
      self.liftdrag_predsplot = self.GUIapp.draw_liftdrag_plots(xs, ys_preds, self.visible_duration, self.params, self.downsample_mult, self.use_compensated_strains, True)
    if mfcest:
      self.MFCplot = self.GUIapp.draw_MFCshapes()    
    eststream_thr = Thread(target=self.stream_estimates, args=(self.GUIapp.liftdragest_list, self.GUIapp.shape_list, ys_preds, stallest, liftdragest, mfcest))
    eststream_thr.start()
    print ("Initialized estimates")

  def stream_estimates(self, liftdragest_list, shape_list, ys_preds, stallest, liftdragest, mfcest):
    plot_type = 'contour'
    blit = True
    while True: #Wait
      if not self.streamhold_queue.empty():
        print ("Started streaming estimates")
        if stallest:
          self.GUIapp.update_stallest_lbls(start_time=time.time())
        if liftdragest:
          self.GUIapp.update_liftdrag_lbls(predictions=True, start_time=time.time()) 
          _ = FuncAnimation(self.liftdrag_predsplot.fig, self.liftdrag_predsplot.plot_live, fargs=(ys_preds, liftdragest_list, self.use_compensated_strains, True, time.time()), interval=self.plot_refresh_rate*1000, blit=True) #DOESN'T REMOVE FROM liftdragest_queue
          time.sleep(0.3)
        if mfcest:
          _ = FuncAnimation(self.MFCplot.fig, self.MFCplot.plot_live, fargs=(shape_list, plot_type, blit, time.time()), interval=self.plot_refresh_rate*1000, blit=blit) #Removes from mfcestimates_queue 
          time.sleep(0.25)
        self.GUIapp.update()
        break
      else:
        pass
    