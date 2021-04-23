# Import packages
import numpy as np
import cv2 
import pytesseract 
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/Cellar/tesseract/4.1.1/bin/tesseract'

def digitize_airspeed (airspeed_vid_path):
  vid = cv2.VideoCapture(airspeed_vid_path)
  fps = int(vid.get(cv2.CAP_PROP_FPS))
  num_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
  vid_dur = int(num_frames/fps)
  
  ys = np.zeros(vid_dur) #Output files

  #Go through 1-second intervals to capture airspeed
  for i in range(vid_dur):
    vid.set(cv2.CAP_PROP_POS_MSEC, i*1000)
    ret, frame = vid.read()

    # Extract the area that includes airspeed info
    cropped = frame[47:73, 3:85] #(y,x)
    # cropped = frame[38:66, 3:85] #(y,x) If trimmed via Lumafusion to 1136x640 resolution

    #Apply OCR to target area
    custom_oem_psm_config = r'--oem 0 -c tessedit_char_whitelist=.0123456789' #Here oem 0 is critical so we don't use LSTM stuff.
    airspeed = pytesseract.image_to_string(cropped, config=custom_oem_psm_config)
    
    #Fix OCR issues
    airspeed = airspeed.replace("\n\x0c", "")
    airspeed = "".join(airspeed.split())
    try:
      if airspeed[-1] == ".":
        airspeed = airspeed[0:-1]
    except:
      airspeed = ys[i-1]

    #Write airspeed to our numpy array.
    try:
      airspeed = float(airspeed)
      ys[i] = airspeed
    except:
      ys[i] = ys[i-1]
      print ("Couldn't read video at time {} (second)".format(i))

  return ys