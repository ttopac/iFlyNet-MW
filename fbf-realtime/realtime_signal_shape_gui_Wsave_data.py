import realtime_signal_shape_gui
sys.path.append(os.path.abspath('./helpers'))
import daq_savedata

import numpy as np
from tkinter import Tk

if __name__ == "__main__":
  #Define show parameters
  params = dict()
  params["sample_rate"] = 1700 #NI uses sample rate values around this, not exactly this.
  visible_duration = 30 #seconds
  plot_refresh_rate = 0.2 #seconds
  downsample_mult = 1
  ys = np.zeros((16,int(visible_duration*params["sample_rate"]/downsample_mult)))
  video_names = ("Side view of the outer MFC", "Side-view of wing fixture")
  camnums = (1,0)

  #Define save parameters
  save_duration = 60 #seconds
  save_path = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/Offline_Tests/offline1Oct6'
  saver = daq_savedata.DataSaverToNP(save_path)
  
  #Start he GUI
  root = Tk()
  root.title ("Real-time Raw Signal and Estimated Shape")

  app = realtime_signal_shape_gui.RawSignalAndShapeWindow(parent=root)
  app.getSGoffsets(params)
  app.draw_videos(video_names, camnums, save_video=True)
  app.plot_signals(ys, visible_duration, downsample_mult, params, plot_refresh_rate, plot_compensated_strains=False, onlyplot=False, data_saver=saver)
  app.draw_MFCshapes(params, plot_refresh_rate)
  root.mainloop()