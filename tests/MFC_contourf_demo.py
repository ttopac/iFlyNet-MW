#Demo contourf plotting for MFC. Note that this script doesn't work with plt.show() with Blit=True due to a bug.

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import MaxNLocator
from matplotlib import cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk


class MFCContourDemo():
  def __init__(self):
    self.fig = plt.figure(figsize=(4.75, 3.50)) #(width, height)
    self.ax = self.fig.add_subplot(111)

    self.xgrid, self.ygrid = np.meshgrid(XVAL, YVAL)
    self.zvals = np.random.rand(self.xgrid.shape[0], self.xgrid.shape[1])
    self.xrootgrid, self.yrootgrid = np.meshgrid(XVALROOT, YVALROOT)
    self.xlegrid, self.ylegrid = np.meshgrid(XVALLE, YVALLE)
    
    self.ax.set_xlabel('Chord (x)', labelpad=0, fontsize=12)
    self.ax.set_ylabel('Span (y)', labelpad=0, fontsize=12)
    self.ax.tick_params(labelsize="small")
    self.ax.set_xlim(-250, 150)
    self.ax.set_ylim(-125, 350)
    self.levels = MaxNLocator(nbins=15).tick_values(-3,3)


  def plot_twod_contour(self):
    self.mysurf = [self.ax.contourf (self.xgrid, self.ygrid, self.zvals, levels=self.levels, cmap=cm.coolwarm)]
    self.mysurf.append(self.ax.contourf (self.xrootgrid, self.yrootgrid, np.zeros_like(self.xrootgrid), levels=self.levels, cmap=cm.coolwarm))
    self.mysurf.append(self.ax.contourf (self.xlegrid, self.ylegrid, np.zeros_like(self.xlegrid), levels=self.levels, cmap=cm.coolwarm))
    colorbar = self.fig.colorbar(self.mysurf[0], shrink=0.6, aspect=10)
    colorbar.set_label("Displacement (mm)")
    self.ax.set_aspect('equal')

  def plot_live(self, i):
    for tp in self.mysurf[0].collections:
      tp.remove()
    self.zvals += np.random.rand(self.xgrid.shape[0], self.xgrid.shape[1])/10
    self.mysurf[0] = self.ax.contourf (self.xgrid, self.ygrid, self.zvals, levels=self.levels, cmap=cm.coolwarm)
    return self.mysurf[0].collections


if __name__ == '__main__':
  root = tk.Tk()
  root.title ("MFC contourf demo")

  XVAL = np.arange(0,101,4) #chord-wise
  YVAL = np.arange(0,305,4) #span-wise
  XVALROOT = np.linspace (-205, 100, 4)
  YVALROOT = np.linspace (-76, 0, 4)
  XVALLE = np.linspace (-205, 0, 4)
  YVALLE = np.linspace (0, 304, 4)
  mfcdemo = MFCContourDemo()
  mfcdemo.plot_twod_contour()

  canvas = FigureCanvasTkAgg(mfcdemo.fig, master=root)
  canvas.get_tk_widget().grid(column=0, row=0)
  ani = FuncAnimation(mfcdemo.fig, mfcdemo.plot_live, interval=400, blit=True)
  root.mainloop()