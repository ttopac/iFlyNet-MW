import sys, os
import time
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
from multiprocessing import Process, Queue


class SaveVideoAndSignals():
  def __init__ (self, preview):
    self.preview = preview

  def skip_preview_button(self):
    button = Button(self.preview, text = 'Happy with the previews? Continue...', command=self.skip_preview)
    button.grid(row=17, column=0, rowspan=1, columnspan=1, sticky=S)

  def skip_preview(self):
    self.preview.video1.endo_video.stopflag = True
    self.preview.video2.endo_video.stopflag = True
    self.save_videos()
    save_signal_flag = True

  def save_videos (self):
    print ("Starting to save videos.")
    
    video1 = daq_capturevideo_helper.SaveVideoCapture(video_titles[0], camnums[0], save_path, save_duration)
    self.video1 = video1
    t1 = Thread(target=video1.multithreaded_save, args=(33, True))    
    video2 = daq_capturevideo_helper.SaveVideoCapture(video_titles[1], camnums[1], save_path, save_duration)
    self.video2 = video2
    t2 = Thread(target=video2.multithreaded_save, args=(33, True))
    
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
  video_titles = ("Side view of the outer MFC", "Side view of wing fixture")
  camnums = (0,1)

  #Define save parameters
  save_path = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Offline_Tests/offline1_Oct6/'
  save_duration = 20 #seconds
  saver = daq_savedata.DataSaverToNP(save_path)
  save_signal_flag = False
  
  #Start he GUI
  root = Tk()
  root.title ("Video previews")

  #Define TK windows
  preview = realtime_signal_shape_gui.RawSignalAndShapeWindow(parent=root)
  main = SaveVideoAndSignals(preview)

  #Display the videos for preview
  preview.getSGoffsets(params)
  preview.draw_videos(video_titles, camnums)
  preview.plot_signals(ys, visible_duration, downsample_mult, params, plot_refresh_rate, plot_compensated_strains=False, onlyplot=False, data_saver=saver, save_duration=save_duration)
  preview.draw_MFCshapes(params, plot_refresh_rate)
  main.skip_preview_button()
  root.mainloop()
  
  print ("End")