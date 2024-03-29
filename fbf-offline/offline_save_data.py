import sys
import os
import time
from tkinter import Tk, Button

sys.path.append(os.path.abspath('./helpers'))
sys.path.append(os.path.abspath('./fbf-realtime'))
sys.path.append(os.path.abspath('./utils'))
import daq_capturedata_helper
import daq_savedata_helper
import gui_windows_helper
import streamdata_helper
import daq_captureANDstreamvideo_helper
import procestimates_helper
import remove_extra_frames

import numpy as np
from tkinter import Tk
from tkinter import N, S, W, E
from threading import Thread
from multiprocessing import Process, Queue, Pipe

save_signal_flag = False
mfcplot_exists = False

class SaveVideoAndSignals():
  def __init__ (self, root, preview, params, save_duration, saveflag_queue, saver, preview_while_saving=False):
    self.root = root
    self.preview = preview
    self.params = params
    self.save_duration = save_duration
    self.saveflag_queue = saveflag_queue
    self.saver = saver
    self.preview_while_saving = preview_while_saving

  def skip_preview_button(self):
    button = Button(self.root, text = 'Happy with the previews? Continue with save...', command=self.skip_preview)
    button.grid(row=0, column=0, rowspan=1, columnspan=1, sticky=S)

  def skip_preview(self):
    if self.preview_while_saving: #KEEP PREVIEW
      self.saveflag_queue.put(True)
      self.save_videos()

    else: #KILL PREVIEW
      #Stop camera plotting and DAQ altogether.
      self.preview.get_data_proc.terminate()
      if mfcplot_exists:
        self.preview.draw_MFC_proc.terminate()
      for video in self.preview.videos:
        video.capture_stopflag = True
      
      #Restart stuff. First initialize videos.
      self.init_videos()
      
      #Then start DAQ 
      parent_conn, child_conn = Pipe()
      send_data_size = int(self.params["sample_rate"]*self.save_duration)
      save_data_proc = Process(target = daq_capturedata_helper.send_data, args=(self.preview.SGoffsets, self.params["sample_rate"], send_data_size, "fixedlen", child_conn, self.saveflag_queue))
      save_data_proc.start()

      #Then start saving videos once DAQ is ready
      while True: #Wait
        if self.saveflag_queue.qsize() > 0:
          _ = self.saveflag_queue.get()
          self.saveflag_queue.put(True) #Start collecting data as soon as video recording starts.
          break #Break when DAQ is ready to capture data 
      time.sleep(1.25) #Obtained empirically. ni_daqmx.reader.read_many_sample starts with about 1.25 sec delay after the command.
      self.save_videos()

      #Save the data once we receive it.
      read_data = parent_conn.recv()
      save_data_proc.join()
      self.saver.save_to_np(read_data)
      
      time.sleep(2) #Wait a little for video to finish.
      for video in self.preview.videos:
        video.endo_video.stopflag=True
      self.vid_thr1.join()
      self.vid_thr2.join()
      self.preview.destroy()
      self.root.destroy()


  def init_videos (self):
    print ("Starting to save videos.")
    save1 = daq_captureANDstreamvideo_helper.SaveVideoCapture(self.preview.videos[0].endo_video, camnums[0], save_path, save_duration, 30)
    save2 = daq_captureANDstreamvideo_helper.SaveVideoCapture(self.preview.videos[1].endo_video, camnums[1], save_path, save_duration, 30)
    self.vid_thr1 = Thread(target=save1.multithreaded_save, args=(time.time_ns(),))    
    self.vid_thr2 = Thread(target=save2.multithreaded_save, args=(time.time_ns(),))
  
  def save_videos (self):
    self.vid_thr1.start()
    self.vid_thr2.start()
    

if __name__ == "__main__":
  #Define show parameters
  params = dict()
  params["sample_rate"] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.2 #seconds
  downsample_mult = 1 #Use 1 for training, use 233 for drifttest.
  ys = np.zeros((18,int(visible_duration*params["sample_rate"]/downsample_mult)))
  video_names = ("Disabled", "AoA Cam")
  camnums = (1,0)
  use_compensated_strains_forstream = False

  #Define save parameters
  save_path = 'g:/Shared drives/WindTunnelTests-Feb2019/July2022_Tests_SNIC/Offline_Tests/offline13_July23/'
  save_duration = 30 #seconds
  saver = daq_savedata_helper.DataSaverToNP(save_path)
  saveflag_queue = Queue() #Queue for sending save flag. Used differently in fixedlen and continuous capture.
  preview_while_saving = False #!!!Previewing while saving is not tested extensively. It may cause data loss or bad quality. Use with caution. Especially, don't use fast refresh!
  #Start the GUI
  root = Tk()
  root.title ("Video previews")

  #Define TK windows
  preview = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(root, plot_refresh_rate, downsample_mult, offline=False)
  main = SaveVideoAndSignals(root, preview, params, save_duration, saveflag_queue, saver, preview_while_saving)
  
  #Get and save SG and RTD offsets
  preview.getSGoffsets(params)
  np.save(save_path+'SG_offsets.npy', preview.SGoffsets)
  
  #Display the videos and wing shape for preview
  preview.draw_videos(video_names, camnums)

  #Initialize data structure
  preview.initialize_queues_or_lists()

  if preview_while_saving:
    preview.start_datacapture_process(params)
  else:
    preview.start_datacapture_process(params, saveflag_queue=saveflag_queue, save_duration=save_duration, saver=saver)

  stream = streamdata_helper.StreamRealTime(preview, params, use_compensated_strains_forstream, downsample_mult, visible_duration, plot_refresh_rate)
  stream.init_sensordata(mfcplot_exists)

  queue_refresh_thread = Thread(target=stream.refresh_queues)
  queue_refresh_thread.start()

  #Place the elements on GUI
  if mfcplot_exists:
    preview.place_on_grid('signal with MFC')
  else:
    preview.place_on_grid('signal only')

  #Save the data
  main.skip_preview_button()
  root.mainloop()

  #Stop queue_refresh_thread
  stream.visible_duration = 0 #We send this to stop the thread.
  queue_refresh_thread.join()
  
  #Finally deframe the videos
  fps = 30
  video_size = (640, 360)
  remove_extra_frames.deframe_video(save_path, save_duration, fps, video_size)

  print ("End!")