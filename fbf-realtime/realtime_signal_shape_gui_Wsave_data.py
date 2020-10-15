import sys, os
import time
import realtime_signal_shape_gui
sys.path.append(os.path.abspath('./helpers'))
import daq_savedata

import numpy as np
from tkinter import Tk

class SaveVideoAndSignals():
  def __init__ (self, ):
    pass

  def save_video (self):
    #Passed
    pass

  def save_signal (self):
    pass

if __name__ == "__main__":
  #Define show parameters
  params = dict()
  params["sample_rate"] = 1700 #NI uses sample rate values around this, not exactly this.
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.2 #seconds
  downsample_mult = 1
  ys = np.zeros((17,int(visible_duration*params["sample_rate"]/downsample_mult)))
  video_names = ("Side view of the outer MFC", "Side view of wing fixture")
  camnums = (0,1)

  #Define save parameters
  save_duration = 20 #seconds
  save_path = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Offline_Tests/offline1_Oct6/'
  saver = daq_savedata.DataSaverToNP(save_path)
  
  #Start he GUI
  root = Tk()
  root.title ("Video previews")

  #First display the videos for preview
  preview = realtime_signal_shape_gui.RawSignalAndShapeWindow(parent=root)
  preview.draw_videos(video_names, camnums, save_video=False)
  input ("If happy with videos, press enter to continue...")
  root.destroy()

  #Capture the SG offsets
  # preview.getSGoffsets(params)
  # SGOffsets = preview.SGoffsets
  # print ("SG offsets are captured.")

  