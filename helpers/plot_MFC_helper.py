import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import sys, os
from matplotlib import cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
sys.path.append(os.path.abspath('./helpers'))
import proc_MFCshape_helper
import tkinter as tk
from multiprocessing import Process, Queue



class PlotMFCShape:
  def __init__(self, plot_refresh_rate, XVAL, YVAL):
    self.plot_refresh_rate = plot_refresh_rate
    self.fig = plt.figure(figsize=(3.75, 3.75))
    plt.subplots_adjust(left=0, bottom=0, right=0.85, top=1.13, wspace=0, hspace=0)

    # self.ax = self.fig.add_subplot(1,1,1)
    self.ax = self.fig.gca(projection='3d')
    self.xgrid, self.ygrid = np.meshgrid(XVAL, YVAL)
    
    self.ax.set_xlabel('chord (x)', labelpad=-12, fontsize=11)
    self.ax.set_ylabel('span (y)', labelpad=-12, fontsize=11)
    self.ax.set_zlabel('3D displacement (mm)', labelpad=4, fontsize=11)
    # self.ax.set_xticklabels([])
    # self.ax.set_yticklabels([])
    self.ax.tick_params(labelsize="small")
    # self.ax.view_init(azim=0, elev=90)

    self.ax.set_zlim(-2, 2)
    # self.ax.auto_scale_xyz([0, 300], [0, 300], [-2, 2])

  def plot_twod_contour(self):
    self.mysurf = self.ax.scatter(self.xgrid, self.ygrid, np.zeros((self.xgrid.shape[0], self.xgrid.shape[1])))
    self.origoffsets = self.mysurf._offsets
    # self.fig.colorbar(self.mysurf, shrink=0.5, aspect=5)

    # Create fake bounding box for scaling
    minz, maxz = -3, 3 #mm
    max_range = np.array([self.xgrid.max() - self.xgrid.min(), self.ygrid.max() - self.ygrid.min(), maxz - minz]).max()
    Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (self.xgrid.max() + self.xgrid.min())
    Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (self.ygrid.max() + self.ygrid.min())
    Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (maxz + minz)
    # Uncomment following both lines to test the fake bounding box:
    # for xb, yb, zb in zip(Xb, Yb, Zb):
    #   self.ax.plot([xb], [yb], [zb], 'w')

  def plot_live(self, i, queue):
    while queue.qsize() > 1: #This is here to keep up with the delay in plotting.
      try:
        a = queue.get_nowait()
      except:
        pass
    try:
      read_shape = queue.get()
      # three_d_vertices = [list(zip(self.xgrid.reshape(-1), self.ygrid.reshape(-1), read_shape.reshape(-1)))] #Attempt to plot with blit, but doesn't seem to be working
      self.mysurf.set_offsets(self.origoffsets)
      self.mysurf.set_3d_properties(read_shape.T.flatten(), '-z')
      # self.mysurf.remove()
      # self.mysurf, = self.ax.plot_surface(self.xgrid, self.ygrid, read_shape.T, cmap=cm.coolwarm, shade=True, vmin=-0.75, vmax=0.75, linewidth=0)
    except:
      pass  
    return (self.mysurf,)


if __name__ == "__main__":
  #Test plotting in TK with fake data streaming in real-time.
  root = tk.Tk()
  root.title ("MFC Plotting")
  plot_refresh_rate = 1 #seconds

  mfc_shape = proc_MFCshape_helper.CalcMFCShape()
  q1 = Queue()
  p1 = Process(target = mfc_shape.supply_data, args=(q1, False, True))
  p1.start()

  plot = PlotMFCShape(plot_refresh_rate, mfc_shape.XVAL, mfc_shape.YVAL)
  plot.plot_twod_contour()

  canvas = FigureCanvasTkAgg(plot.fig, master=root)
  canvas.get_tk_widget().grid(column=0, row=1)
  ani = FuncAnimation(plot.fig, plot.plot_live, fargs=(q1,), interval=plot_refresh_rate*1000, blit=False)
  root.mainloop()