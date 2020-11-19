import time
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
import sys, os
from matplotlib import cm
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
sys.path.append(os.path.abspath('./helpers'))
import proc_MFCshape_helper
import tkinter as tk
from multiprocessing import Process, Queue


class PlotMFCShape:
  def __init__(self, plot_refresh_rate, XVAL, YVAL, offline=False):
    self.plot_refresh_rate = plot_refresh_rate
    self.XVAL = XVAL
    self.YVAL = YVAL
    self.fig = plt.figure(figsize=(4.75, 3.25)) #(width, height)
    self.xgrid, self.ygrid = np.meshgrid(XVAL, YVAL)
    self.levels = MaxNLocator(nbins=15).tick_values(-3,3)
    self.offline = offline

  
  # def gen_vertices(self, Z): #OBSOLETE. THIS IS NOT USEFUL SINCE PLOT_SURFACE WITH BLIT DOESN'T MAKE ANYTHING FASTER.
  #   Xn,Yn,Zn = np.broadcast_arrays(self.xgrid, self.ygrid, Z)
  #   rows, cols = Zn.shape
  #   stride=1 #This should be same as the downsampling number in proc_MFC_helper
  #   row_inds = list(range(0, rows-1, stride)) + [rows-1]
  #   col_inds = list(range(0, cols-1, stride)) + [cols-1]

  #   polys = []
  #   for rs, rs_next in zip(row_inds[:-1], row_inds[1:]):
  #     for cs, cs_next in zip(col_inds[:-1], col_inds[1:]):
  #       ps = [cbook._array_perimeter(a[rs:rs_next+1, cs:cs_next+1]) for a in (Xn, Yn, Zn)]
  #       ps = np.array(ps).T
  #       polys.append(ps)
  #   npolys = np.asarray(polys).reshape(-1,3)
  #   return npolys


  def init_plot(self, plot_type):
    if plot_type == "contour":
      self.plot_2D_contour()
    elif plot_type == "surface":
      self.plot_3D_surface()


  def plot_3D_surface(self):
    plt.subplots_adjust(left=0, bottom=0, right=1.02, top=1.02, wspace=0, hspace=0)
    self.ax = plt.subplot(111, projection='3d')
    self.ax.set_xlabel('chord (x)', labelpad=-12, fontsize=11)
    self.ax.set_ylabel('span (y)', labelpad=-12, fontsize=11)
    self.ax.set_zlim(-3, 3)
    self.ax.set_xticklabels([])
    self.ax.set_yticklabels([])
    self.ax.set_zticklabels([])
    self.ax.tick_params(labelsize="small")
    self.mysurf = self.ax.plot_surface(self.xgrid, self.ygrid, np.zeros((self.xgrid.shape[0], self.xgrid.shape[1])), cmap=cm.coolwarm, shade=True, vmin=-3, vmax=3, linewidth=0)
    colorbar = self.fig.colorbar(self.mysurf, shrink=0.6, aspect=10)
    colorbar.set_label("Displacement (mm)", fontsize=12)
    colorbar.ax.tick_params(labelsize="x-small")
    
    # Create fake bounding box for scaling
    minz, maxz = -3, 3 #mm
    max_range = np.array([self.xgrid.max() - self.xgrid.min(), self.ygrid.max() - self.ygrid.min(), maxz - minz]).max()
    Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (self.xgrid.max() + self.xgrid.min())
    Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (self.ygrid.max() + self.ygrid.min())
    Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (maxz + minz)
    for xb, yb, zb in zip(Xb, Yb, Zb):
      self.ax.plot([xb], [yb], [zb], 'w')


  def plot_2D_contour(self):
    XVALROOT = np.linspace (-205, 100, 4)
    YVALROOT = np.linspace (-76, 0, 4)
    XVALLE = np.linspace (-205, 0, 4)
    YVALLE = np.linspace (0, 304, 4)
    self.xrootgrid, self.yrootgrid = np.meshgrid(XVALROOT, YVALROOT)
    self.xlegrid, self.ylegrid = np.meshgrid(XVALLE, YVALLE)

    self.ax = plt.subplot(111)
    self.ax.set_xlabel('Chord (x)', labelpad=0, fontsize=12)
    self.ax.set_ylabel('Span (y)', labelpad=0, fontsize=12)
    self.ax.set_xticklabels([])
    self.ax.set_yticklabels([])
    self.ax.set_aspect('equal')
    self.ax.set_xlim(-250, 150)
    self.ax.set_ylim(-125, 350)
    self.ax.tick_params(labelsize="small")

    self.mysurf = [self.ax.contourf (self.xgrid, self.ygrid, np.random.rand(self.xgrid.shape[0], self.xgrid.shape[1]), levels=self.levels, cmap=cm.coolwarm)]
    self.mysurf.append(self.ax.contourf (self.xrootgrid, self.yrootgrid, np.zeros_like(self.xrootgrid), levels=self.levels, cmap=cm.coolwarm))
    self.mysurf.append(self.ax.contourf (self.xlegrid, self.ylegrid, np.zeros_like(self.xlegrid), levels=self.levels, cmap=cm.coolwarm))
    colorbar = self.fig.colorbar(self.mysurf[0], shrink=0.6, aspect=10)
    colorbar.set_label("Displacement (mm)", fontsize=12)
    colorbar.ax.tick_params(labelsize="x-small")



  def plot_live(self, i, queue, plot_type, blit, start_time=None):
    try:
      if not self.offline:
        read_shape = queue.get()
        queue.put_nowait(read_shape)
      else:
        t0 = time.time()
        cur_frame = int((t0-start_time)/self.plot_refresh_rate)
        read_shape = queue[cur_frame]  
          
      if plot_type == "contour":
        if blit == True:
          for tp in self.mysurf[0].collections:
            tp.remove()
          self.mysurf[0] = self.ax.contourf (self.xgrid, self.ygrid, read_shape.T, levels=self.levels, cmap=cm.coolwarm)
          return self.mysurf[0].collections
        else:
          self.mysurf[0].remove()
          self.mysurf[0] = self.ax.contourf (self.xgrid, self.ygrid, read_shape.T, levels=self.levels, cmap=cm.coolwarm)

      elif plot_type == "surface": #Assume blit=False
        self.mysurf.remove()
        self.mysurf = self.ax.plot_surface(self.xgrid, self.ygrid, read_shape.T, cmap=cm.coolwarm, shade=True, vmin=-3, vmax=3, linewidth=0)
    except:
      pass  


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