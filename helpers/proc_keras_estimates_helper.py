import keras
import tensorflow
from keras.models import load_model
from keras.layers import LeakyReLU
import numpy as np

means = [-2.0175109479796352e-05, 0.00010905074475577042, 0.000394543100057414, -0.00028464991647680427, -0.0005756637708546992, -6.731485416880471e-05, -95.96163203982827, -24.0868367686678]
stddevs = [0.0012517186084292822, 0.0018231860855292457, 0.0010487415470856675, 0.0027847121382814344, 0.0013364316889671896, 0.00208186772161978, 108.47167144875641, 19.360939493624215]
leakyrelu = LeakyReLU(alpha=0.05)

class iFlyNetEstimates:
  def __init__(self, pred_freq, stall_model_path, liftdrag_model_path):
    self.pred_freq = pred_freq
    self.stall_model = load_model(stall_model_path, custom_objects={'LeakyReLU': leakyrelu})
    self.liftdrag_model = load_model(liftdrag_model_path, custom_objects={'LeakyReLU': leakyrelu})
    self.means = means
    self.stddevs = stddevs

  def estimate_stall (self, sensordata):
    # Standardize sensordata shape= (8, -1) PZT + COMMSG data
    sensordata_rshp = sensordata.reshape(sensordata.shape[0], -1, self.pred_freq) #WORKED shape= (8, -1, 233) for Sept. 2020
    sensordata_rshp_t = np.transpose(sensordata_rshp, (1,2,0)) #WORKED shape= (-1, 233, 8) for Sept. 2020.
    sensordata_rshp_t_std = (sensordata_rshp_t-self.means)/self.stddevs 
    preds = self.stall_model.predict(sensordata_rshp_t_std)
    cond = preds[:,0] < 0.5 #NoStall: False
    return cond

  def estimate_liftdrag (self, sensordata):
    # Standardize sensordata
    sensordata_rshp = sensordata.reshape(sensordata.shape[0], -1, self.pred_freq)
    sensordata_rshp_t = np.transpose(sensordata_rshp, (1,2,0))
    sensordata_rshp_t_std = (sensordata_rshp_t-self.means[0:6])/self.stddevs[0:6]
    preds = self.liftdrag_model.predict(sensordata_rshp_t_std)

    # De-standardize predictions
    destd_preds = preds*self.stddevs[6:]+self.means[6:]
    return destd_preds