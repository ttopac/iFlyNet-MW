#Steps for trimming + deframing anemometer video.
#1) Determine the time to start the video (tested with lumafusion on ipad)
#2) Trim with ffmpeg. Sample command: ffmpeg -ss 00:00:54.50 -i anemometer_orig.mp4 -c copy -t 00:05:00.33 anemometer_cut.mp4
#3) Deframe with this script.

import cv2
import os

def deframe_video(folder, req_len, fps, video_size):
  frames_to_remove = set()

  for file in os.listdir(folder):
    if file.startswith("video") and file.endswith(".mp4"): #For side cam videos
    # if file.startswith("anemometer_cut") and file.endswith(".mp4"): #For anemometer videos
      video_writer = cv2.VideoWriter(folder+'deframed_'+file[:-4]+'.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, video_size)        
      cap = cv2.VideoCapture(folder+file)
      length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
      diff = length - req_len*fps
      for i in range(diff):
        frames_to_remove.add(length/diff*i)
      for i in range(length):
        try:
          _, frame = cap.read()
          if i not in frames_to_remove:
            video_writer.write(frame)
        except:
          pass
      video_writer.release()
      print ("Video {} is deframed".format(file))


if __name__ == '__main__':
  # main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/Offline_Tests/'
  main_folder = '/Volumes/Macintosh HD/Users/tanay/OneDrive - Stanford/Sept2020_Tests/Offline_Tests/'
  test_folder = 'offline12_Dec16/'
  req_len = 300 #seconds
  fps = 30
  video_size = (640, 360) #For side cam videos
  # video_size = (1168, 672) #For anemometer videos
  deframe_video(main_folder+test_folder, req_len, fps, video_size)

