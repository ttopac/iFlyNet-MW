from collections import deque
import collections
import platform
import subprocess
import cv2

import numpy as np
import tkinter as tk
from tkinter import Tk, Frame, Canvas, Label
from tkinter import N, S, W, E
import PIL.Image, PIL.ImageTk
from threading import Thread
from multiprocessing import Process, Queue
import time


class CaptureVideoWEndoscope:
  def __init__ (self, camnum):
    self.cap = cv2.VideoCapture(camnum)
    if not self.cap.isOpened():
      raise ValueError("Unable to open video source", camnum)
    self.cap.set(3,1280)
    self.cap.set(4,720)
    self.viddeque = deque(maxlen=1)  # Initialize deque used to store frames read from the stream
    w = self.cap.get(3)
    h = self.cap.get(4)
    self.new_w = int(w/2)
    self.new_h = int(h/2)
    self.size = (self.new_w, self.new_h)
    self.stopflag = False

  def show_video_standalone (self):
    while(True):
      if self.cap.isOpened():
        # Capture frame-by-frame
        ret, frame = self.cap.read()
        # Make adjustments to the frame
        resized = cv2.resize(frame, (self.new_w, self.new_h)) 
        # Display the resulting frame
        cv2.imshow('frame', resized)
        if cv2.waitKey(1) & 0xFF == ord('q'):
          break

  def get_frames (self, multithreaded=False, append_time=time.time()): #Multithreaded is recommended for more than 1 camera
    if multithreaded:
      while True:
        if self.cap.isOpened():
          ret, frame = self.cap.read()
          if ret:
            resized = cv2.resize(frame, (self.new_w, self.new_h))
            self.viddeque.append(resized)
        if self.stopflag:
          break

    else:
      if self.cap.isOpened():
        ret, frame = self.cap.read()
        resized = cv2.resize(frame, (self.new_w, self.new_h)) 
        if ret:
          return (ret, cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))

  def destroy_video_for_TK (self):
    if self.cap.isOpened():
      self.cap.release()

class SaveVideoCapture():
  def __init__(self, endo_video, camnum, save_path, save_duration, fps):
    self.endo_video = endo_video
    self.camnum = camnum
    self.save_path = save_path
    self.save_duration = save_duration
    self.delay = 1/fps
    self.video_writer = cv2.VideoWriter(self.save_path+'video'+str(self.camnum)+'.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, self.endo_video.size)        
  
  def multithreaded_save(self, starttime=time.time_ns()):
    frame = 0
    starttime = time.time_ns() #Correct starttime between process definition and process start.
    print("Recording first frame at {}.".format(time.time()))
    writestart_time = starttime
    while True:
      cv2image = self.endo_video.viddeque[-1]
      while ((time.time_ns() - (writestart_time - 0.0008*1e9))/1e9 < self.delay): #This - 0.0008 is empirical to negate the delay we couldn't pinpoint.
        pass
      writestart_time=time.time_ns()
      self.video_writer.write(cv2image)
      if (time.time_ns()-starttime)/1e9 > self.save_duration:
        self.video_writer.release()
        print ("Video created at {}.".format(time.time()))
        break
      frame += 1


class DrawTKVideoCapture(Frame):
  def __init__(self, parent, window_title, camnum):
    Frame.__init__(self,parent)
    self.window_title = window_title
    self.camnum = camnum
    self.parent = parent
    self.endo_video = CaptureVideoWEndoscope(self.camnum)
    self.capture_stopflag = False
    self.videocvs = Canvas(self.parent, width=self.endo_video.new_w, height=self.endo_video.new_h)
    self.videolbl = Label(self.parent, text=window_title, font=("Helvetica", 18))

  def capture(self, delay=15):    
      ret, frame = self.endo_video.get_frames()
      if ret:
        self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
        if self.video == None:
          self.video = self.videocvs.create_image(0,0,image = self.photo, anchor = tk.NW)
        else: 
          self.videocvs.itemconfig(self.video, image=self.photo) #Added on Nov15,2020 but not tested. Remove if causing issues...
          self.videocvs.image = self.photo #Added on Nov15,2020 but not tested. Remove if causing issues...
      self.parent.after(delay, self.capture, delay)

  def place_on_grid (self, row, column, rowspan, columnspan):
    self.videocvs.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan)
    self.videolbl.grid(row=row-1, column=column, rowspan=1, columnspan=columnspan, sticky=S)

  def multithreaded_capture(self, delay=33, init_call=False):
    if init_call:
      self.videocount = 0
      self.thr = Thread(target=self.endo_video.get_frames, args=(True,time.time()))
      self.thr.start()
    
    try:
      cv2image = self.endo_video.viddeque[-1]
      tkimage = PIL.Image.fromarray(cv2.cvtColor(cv2image, cv2.COLOR_BGR2RGB))
      self.photo = PIL.ImageTk.PhotoImage(tkimage)
      if self.videocount == 0: 
        self.video = self.videocvs.create_image(0, 0, image=self.photo, anchor=tk.NW)
      else:
        self.videocvs.itemconfig(self.video, image=self.photo)
        self.videocvs.image = self.photo #Added on Nov15,2020 but not tested. Remove if causing issues...
      if self.endo_video.stopflag or self.capture_stopflag:
        self.after (delay, self.videocap_ended)
      else:
        self.videocount += 1
        self.after (delay, self.multithreaded_capture, delay, False)
    except Exception:
      result = None
      while result is None:
        try:
          result = "Passed"
          self.after (delay, self.multithreaded_capture, delay, False)
        except:
          result = None

  def videocap_ended(self):
    print ("Video capture ended.")
    self.parent.destroy()


class DrawTKOfflineVideo(Frame):
  def __init__(self, parent, window_title, camnum, videopath):
    Frame.__init__(self,parent)
    self.parent = parent
    self.window_title = window_title
    self.camnum = camnum
    self.videopath = videopath
    self.videocvs = Canvas(parent, width=640, height=360)
    self.videolbl = Label(parent, text=window_title, font=("Helvetica", 21, 'bold', 'underline'))
    self.draw_and_process_image()

  def draw_and_process_image(self):
    step = 0
    self.frame_photos = list()
    path = self.videopath+'video'+str(self.camnum)+'.mp4'
    
    #Do with openCV
    # self.cap = cv2.VideoCapture(path)
    # if (self.cap.isOpened() == False):  
    #   print("Error opening the video file") 
    #Do with ffmpeg
    args = ["ffmpeg", "-i", path, "-f", "image2pipe", "-pix_fmt", "rgb24", "-vcodec", "rawvideo", "-"]
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=640 * 360 * 3)

    while True:
      try:
        #Do with openCV
        # _, frame = self.cap.read()
        # recolored_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #Do with ffmpeg
        frame = pipe.stdout.read(640 * 360 * 3)
        
        array = np.frombuffer(frame, dtype="uint8").reshape((360, 640, 3))

        frame_photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(array))
        if step == 0:
          self.vidframe = self.videocvs.create_image(0,0,image = frame_photo, anchor = tk.NW)
        self.frame_photos.append (frame_photo)
        step += 1
      except:
        break

  def stream_images(self, start_time, delay=1/30):
    try:
      t0 = time.time()
      cur_frame = int((t0-start_time)/delay)
      frame_photo = self.frame_photos[cur_frame]
      self.videocvs.itemconfig (self.vidframe, image=frame_photo)
      self.videocvs.image = frame_photo
      if time.time() - start_time < 1:
        call_delay = 100
      else:
        call_delay = 30
      
    except Exception as e:
      print (e)
    
    self.parent.after (call_delay, self.stream_images, start_time, delay)


if __name__ == "__main__":
  aoavideo = CaptureVideoWEndoscope(0)
  aoavideo.show_video_standalone()