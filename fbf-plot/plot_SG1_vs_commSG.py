import matplotlib.pyplot as plt
import numpy as np

main_folder = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/'
test_folder = 'Offline_Tests/offline_SG4_300mm_down_Apr4/'
test_file = 'test.npy'

test_dat = np.load(main_folder+test_folder+test_file)
x_arr = np.linspace(0, 60, test_dat.shape[1])

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(x_arr, test_dat[6,:], label="SG1")
ax.plot(x_arr, test_dat[14,:], label="commSG")
ax.legend(fontsize=9, loc="upper right")
ax.set_xlabel("Time (sec)")
ax.set_ylabel("Strain (ue)")
ax.set_title("SG1 vs commSG Bending Down Static Test (300mm)")

plt.show()

