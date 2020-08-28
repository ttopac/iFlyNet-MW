#Run this script to list available NI DAQ devices and their IDs in the system.
#%%
import nidaqmx
system = nidaqmx.system.System.local()
for device in system.devices:
  print (device)
