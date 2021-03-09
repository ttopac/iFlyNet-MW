#This basic script is to store manually digitized AoA readings in a numpy array.

import pandas as pd
import numpy as np

def digitize_aoa (aoa_csv_path):
  aoa_df = pd.read_csv(aoa_csv_path)
  ys = aoa_df['aoa'].to_numpy()
  return ys