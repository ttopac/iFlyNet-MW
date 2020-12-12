import sys
import os
import numpy as np
from tkinter import *
from tkinter import Tk, Frame, Button, Label, Canvas
from threading import Thread

sys.path.append(os.path.abspath('./helpers'))
import gui_windows_helper
import streamdata_helper

main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# main_folder = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'

params = dict()
params["sample_rate"] = 7142 #Use 7142 for training, 1724 for drift. 1724 becomes 1724.1379310344828. 7142 becomes 7142.857142857143 Lowest sample rate possible is 1613 for our NI device. 

if __name__ == "__main__":
  #Define parameters  
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.1 #seconds
  downsample_mult = 233
  use_compensated_strains = False

  root = Tk()
  root.title ("Real-time Video and Signals")
  video_names = ("AoA view", "Outer MFC view")
  camnums = (1,0)

  GUIapp = gui_windows_helper.GroundTruthAndiFlyNetEstimatesWindow(root, plot_refresh_rate, downsample_mult, offline=False)
  GUIapp.getSGoffsets(params)
  GUIapp.initialize_queues_or_lists()
  GUIapp.draw_videos(video_names, camnums)

  GUIapp.captureData(params)
  
  stream = streamdata_helper.StreamRealTime(GUIapp, params, use_compensated_strains, downsample_mult, visible_duration, plot_refresh_rate)
  stream.init_and_stream_sensordata(False)
  queue_refresh_thread = Thread(target=stream.refresh_queues)
  queue_refresh_thread.start()

  GUIapp.place_on_grid(True, False, False)

  root.mainloop()