import sys, os
import time

from numpy.lib.npyio import save
import realtime_signal_shape_gui
from tkinter import Tk, Frame, Button
sys.path.append(os.path.abspath('./helpers'))
import daq_savedata
import daq_capturevideo_helper
import daq_capturedata_helper

import numpy as np
from tkinter import Tk
from tkinter import N, S, W, E
from threading import Thread
from multiprocessing import Process, Queue, Pipe

save_signal_flag = False

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
    button = Button(self.preview, text = 'Happy with the previews? Continue with save...', command=self.skip_preview)
    button.grid(row=17, column=0, rowspan=1, columnspan=1, sticky=S)

  def skip_preview(self):
    if self.preview_while_saving: #KEEP PREVIEW
      self.saveflag_queue.put(True)
      self.save_videos()
      savetime = time.time()

    else: #KILL PREVIEW
      #Stop camera plotting and DAQ altogether.
      self.preview.get_data_proc.terminate()
      self.preview.draw_MFC_proc.terminate()
      self.preview.video1.capture_stopflag = True
      self.preview.video2.capture_stopflag = True
      
      #Restart stuff. First DAQ
      parent_conn, child_conn = Pipe()
      p = Process(target = daq_capturedata_helper.send_data, args=(self.preview.SGoffsets, self.params["sample_rate"], int(self.params["sample_rate"]*self.save_duration), "fixedlen", child_conn, self.saveflag_queue))
      p.start()

      #Then videos
      while True: #Wait
        if self.saveflag_queue.qsize() > 0:
          _ = self.saveflag_queue.get()
          self.saveflag_queue.put(True) #Start collecting data as soon as video recording starts.
          break #Break when DAQ is ready to capture data 
      self.save_videos()

      #Save the data once we receive it.
      read_data = parent_conn.recv()
      p.join()
      self.saver.save_to_np(read_data)
      
      time.sleep(1) #Wait a little for video to finish.
      self.preview.video1.endo_video.stopflag=True
      self.preview.video2.endo_video.stopflag=True
      self.root.destroy()


  def save_videos (self):
    print ("Starting to save videos.")
    save1 = daq_capturevideo_helper.SaveVideoCapture(self.preview.video1.endo_video, video_titles[0], camnums[0], save_path, save_duration)
    t1 = Thread(target=save1.multithreaded_save, args=(1/30, True))    
    save2 = daq_capturevideo_helper.SaveVideoCapture(self.preview.video2.endo_video, video_titles[1], camnums[1], save_path, save_duration)
    t2 = Thread(target=save2.multithreaded_save, args=(1/30, True))
    
    t1.start()
    t2.start()
    

if __name__ == "__main__":
  #Define show parameters
  params = dict()
  params["sample_rate"] = 1700 #NI uses sample rate values around this, not exactly this.
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.2 #seconds
  downsample_mult = 1
  ys = np.zeros((17,int(visible_duration*params["sample_rate"]/downsample_mult)))
  video_titles = ("Side view of the outer MFC", "Side view of the wing fixture")
  camnums = (0,1)

  #Define save parameters
  save_path = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Offline_Tests/offline1_Oct6/'
  save_duration = 20 #seconds
  saver = daq_savedata.DataSaverToNP(save_path)
  saveflag_queue = Queue() #Queue for sending save flag. Used differently in fixedlen and continuous capture.
  preview_while_saving = False #!!!Previewing while saving is not tested extensively. It may cause data loss or bad quality. Use with caution. Especially, don't use fast refresh!
  #Start he GUI
  root = Tk()
  root.title ("Video previews")

  #Define TK windows
  preview = realtime_signal_shape_gui.RawSignalAndShapeWindow(parent=root)
  main = SaveVideoAndSignals(root, preview, params, save_duration, saveflag_queue, saver, preview_while_saving)

  #Display the videos and wing shape for preview
  preview.getSGoffsets(params)
  preview.draw_videos(video_titles, camnums)
  if preview_while_saving:
    preview.plot_signals(ys, visible_duration, downsample_mult, params, plot_refresh_rate, onlyplot=False, plot_compensated_strains=False, saveflag_queue=saveflag_queue, save_duration=save_duration, saver=saver)
    preview.draw_MFCshapes(plot_refresh_rate, 'contour', True)
  else:
    preview.plot_signals(ys, visible_duration, downsample_mult, params, plot_refresh_rate, onlyplot=False, plot_compensated_strains=False)
    preview.draw_MFCshapes(plot_refresh_rate, 'contour', True)

  #Save the data
  main.skip_preview_button()
  root.mainloop()
  
  print ("End!")