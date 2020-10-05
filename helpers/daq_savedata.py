import numpy as np

class DataSaverToNP():
  def __init__(self, filename):
    self.filename = filename

  def save_to_np(self, data):
    np.save(filename+'.np', data)