import cv2
import os


def deframe_video(folder, req_len, fps, video_size):
  frames_to_remove = set()

  for file in os.listdir(folder):
    if file.startswith("video") and file.endswith(".mp4"):
      video_writer = cv2.VideoWriter(folder+file[:-4]+'_deframed.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, video_size)        
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
  main_folder = 'c:/Users/SACL/OneDrive - Stanford/Sept2020_Tests/Offline_Tests/'
  test_folder = 'offline14_Dec16/'
  req_len = 300 #seconds
  fps = 30
  video_size = (640, 360)
  deframe_video(main_folder+test_folder, req_len, fps, video_size)

