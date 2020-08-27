import serial
import time

num_rot = 50
arduinoData=serial.Serial('com3',19200)

for a_iter in range (0, num_rot):
    arduinoData.write (1)
    time.sleep(0.1) # might not needed if the system already have delay
    print('Wing is rotating..%d ' % a_iter)