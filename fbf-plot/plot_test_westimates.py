#This script is used to plot offline lift/drag SG histories overlaid with lift/drag + stall predictions.
import numpy as np
import sys, os
sys.path.append(os.path.abspath('./helpers'))
import plot_commSGs_westimates_helper
import proc_tempcomp_helper

# main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/'
# main_folder = 'g:/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/GoogleDrive/Shared drives/WindTunnelTests-Feb2019/Sept2020_Tests/'
# main_folder = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/'
test_folder, ref_temp = 'test2_Sept19', 20.6590 #Test1_Sept19=21.1350, Test2_Sept19=20.6590 #Reftemp is unique for test_folder and captured at the beginning of experiments
testid = '2'
stall_model_filename = 'stall_train993_val_988'
liftdrag_model_filename = 'lift_train_loss0461'
keras_samplesize=233
test_duration = 60 #seconds
compensate_data = False

test_data = np.load(main_folder+'Training_Tests/{}/test{}.npy'.format(test_folder,testid))
stall_model_path = main_folder+'Kerasfiles/{}.hdf5'.format(stall_model_filename)
liftdrag_model_path = main_folder+'Kerasfiles/{}.hdf5'.format(liftdrag_model_filename)

if __name__ == "__main__":
  end_data = int(test_data.shape[1]/keras_samplesize)*keras_samplesize
  test_data = test_data[:,0:end_data]
  fewerdata = np.mean (test_data.reshape(test_data.shape[0],-1,keras_samplesize), axis=2) #Downsample the SG and temp data
  xs = np.linspace (0, test_duration, fewerdata.shape[1])

  if compensate_data:
    comp = proc_tempcomp_helper.CommSG_Temp_Comp(ref_temp)
    comp_liftdrag, var = comp.compensate (test_data[14:16], test_data[16])
    comp_fewer_liftdrag, fewer_var = comp.compensate (fewerdata[14:16], fewerdata[16])
    test_data[14:16] = comp_liftdrag
    fewerdata[14:16] = comp_fewer_liftdrag

  plots = plot_commSGs_westimates_helper.PlotData(xs, keras_samplesize, stall_model_path, liftdrag_model_path)
  plots.plot_liftdrag_real(fewerdata, ref_temp)
  
  stall_predictors = np.concatenate ((test_data[0:6], test_data[14:16]), axis=0)
  plots.plot_stall_est(stall_predictors)
  
  liftdrag_predictors = test_data[0:6]
  plots.plot_liftdrag_est(liftdrag_predictors)

  plots.term_common_params(False)