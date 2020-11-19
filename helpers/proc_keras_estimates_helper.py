import keras
import tensorflow
from keras.models import load_model
from keras.layers import LeakyReLU
import numpy as np

class iFlyNetEstimates:
  def __init__(self, pred_freq, models):
    self.pred_freq = pred_freq
    self.models = models
    self.means = models ['means']
    self.stddevs = models ['stddevs']

  def estimate_stall (self, sensordata):
    # Standardize sensordata shape= (8, -1) PZT + COMMSG data
    sensordata_rshp = sensordata.reshape(sensordata.shape[0], -1, self.pred_freq) #WORKED shape= (8, -1, 233) for Sept. 2020
    sensordata_rshp_t = np.transpose(sensordata_rshp, (1,2,0)) #WORKED shape= (-1, 233, 8) for Sept. 2020.
    sensordata_rshp_t_std = (sensordata_rshp_t-self.means[0:6-self.models['sensorcuts'][0]]) / self.stddevs[0:6-self.models['sensorcuts'][0]]
    preds = self.models['modelfiles'][0].predict(sensordata_rshp_t_std)
    cond = preds[:,0] < 0.5 #NoStall: False
    return cond

  def estimate_liftdrag (self, sensordata):
    # Standardize sensordata shape= (8, -1) PZT + COMMSG data
    sensordata_rshp = sensordata.reshape(sensordata.shape[0], -1, self.pred_freq)
    sensordata_rshp_t = np.transpose(sensordata_rshp, (1,2,0))
    sensordata_rshp_t_std = (sensordata_rshp_t-self.means[0:6-self.models['sensorcuts'][1]]) / self.stddevs[0:6-self.models['sensorcuts'][1]]
    preds = self.models['modelfiles'][1].predict(sensordata_rshp_t_std)

    # De-standardize predictions
    destd_preds = preds*self.stddevs[-self.models['sensorcuts'][1]]+self.means[-self.models['sensorcuts'][1]]
    return destd_preds