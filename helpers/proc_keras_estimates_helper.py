import numpy as np
import pickle
import time
from sklearn import preprocessing

class iFlyNetEstimates:
  def __init__(self, pred_freq, models):
    self.pred_freq = pred_freq
    self.models = models
    self.means = models ['means']
    self.stddevs = models ['stddevs']

  def estimate_stall (self, sensordata):
    sensordata_rshp = sensordata.reshape(sensordata.shape[0], -1, self.pred_freq) #WORKED shape= (8, -1, 233) for Sept. 2020
    sensordata_rshp_t = np.transpose(sensordata_rshp, (1,2,0)) #WORKED shape= (-1, 233, 8) for Sept. 2020.
    sensordata_rshp_t_std = (sensordata_rshp_t-self.means[np.array(self.models['activesensors'][0])]) / self.stddevs[np.array(self.models['activesensors'][0])]
    preds = self.models['modelfiles'][0].predict(sensordata_rshp_t_std)
    cond = preds[:,0] < 0.5 #NoStall: False
    return cond

  def estimate_state (self, sensordata):
    #Load the state encoder and truth file for decoding.
    encoder_path = self.models['filepaths'][2]+'_encoder.p'
    statetruth_path = self.models['filepaths'][2]+'_statetruth.p'
    with open (encoder_path, "rb") as file_pi:
      encoder = pickle.load(file_pi)
    with open (statetruth_path, "rb") as file_pi:
      statetruth = pickle.load(file_pi)

    #Pre-process and do the prediction.
    sensordata_rshp = sensordata.reshape(sensordata.shape[0], -1, self.pred_freq) #shape= (8, -1, 233) for Sept. 2020
    sensordata_rshp_t = np.transpose(sensordata_rshp, (1,2,0)) #shape= (-1, 233, 8) for Sept. 2020.
    sensordata_rshp_t_std = (sensordata_rshp_t-self.means[np.array(self.models['activesensors'][2])]) / self.stddevs[np.array(self.models['activesensors'][2])]
    ''' 
    The code below can be used measure Keras computation speed:
    data2 = sensordata_rshp_t_std[1000].reshape(1,233,9)
    data3 = sensordata_rshp_t_std[1100].reshape(1,233,9)
    data4 = sensordata_rshp_t_std[1200].reshape(1,233,9)
    t1 = time.time()
    preds = self.models['modelfiles'][2].predict(data2)
    print ("Initial prediction takes {} seconds.".format(time.time() - t1))
    t2 = time.time()
    preds = self.models['modelfiles'][2].predict(data3)
    print ("Second predictions take {} seconds.".format(time.time() - t2))
    t3 = time.time()
    preds = self.models['modelfiles'][2].predict(data4)
    print ("Third predictions take {} seconds.".format(time.time() - t3))
    '''
    preds = self.models['modelfiles'][2].predict(sensordata_rshp_t_std, verbose=0)
    argmax_preds = np.argmax (preds, axis=1)
    _ = encoder.inverse_transform(statetruth) #making encoder remember previous states.
    decoded_preds = encoder.inverse_transform(argmax_preds) #Actually decode predictions.
    
    #Prepare decoded predictions for GUI.
    pretty_preds = np.zeros((decoded_preds.shape[0], 2))
    for i in range(decoded_preds.shape[0]):
      pretty_preds[i,0] = int(decoded_preds[i].split(sep=b'_')[0].split(sep=b'm')[0]) #Airspeed
      pretty_preds[i,1] = int(decoded_preds[i].split(sep=b'_')[1].split(sep=b'd')[0]) #Aoa
      if pretty_preds[i,0] == 4 and pretty_preds[i,1] == 0: #Very nasty workaround for not having 0m/s 0deg label. TODO: investigate
        pretty_preds[i,0] = 0
    return pretty_preds

  def estimate_liftdrag (self, sensordata):
    sensordata_rshp = sensordata.reshape(sensordata.shape[0], -1, self.pred_freq)
    sensordata_rshp_t = np.transpose(sensordata_rshp, (1,2,0))
    sensordata_rshp_t_std = (sensordata_rshp_t-self.means[np.array(self.models['activesensors'][1])]) / self.stddevs[np.array(self.models['activesensors'][1])]
    preds = self.models['modelfiles'][1].predict(sensordata_rshp_t_std, verbose=0)

    # De-standardize predictions
    output_channels = list(set(self.models['activesensors'][0]) - set(self.models['activesensors'][1]))
    destd_preds = preds*self.stddevs[output_channels]+self.means[output_channels]
    return destd_preds