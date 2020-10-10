from collections import deque
import cv2

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

  def get_frames (self, multithreaded=False): #Multithreaded is recommended for more than 1 camera
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
  def __init__(self, endo_video, video_title, camnum, save_path, save_duration):
    self.endo_video = endo_video
    self.video_title = video_title
    self.camnum = camnum
    self.save_path = save_path
    self.save_duration = save_duration
  
  def multithreaded_save(self, delay=1/30, init_call=False):
    if init_call:
      self.videocount = 0
      self.video_writer = cv2.VideoWriter(self.save_path+self.video_title+'.avi', cv2.VideoWriter_fourcc(*'XVID'), 0, self.endo_video.size)        
      starttime = time.time()
    while True:
      try:
        cv2image = self.endo_video.viddeque[-1]
        self.video_writer.write(cv2image)
        if self.videocount == 0: 
          print("First frame recorded.")
        elif time.time()-starttime > self.save_duration:
          self.video_writer.release()
          print ("Video created.")
          print ("!!!Add functionality to change duration of video to what we want!!!")
          break
        self.videocount += 1
      except Exception:
        pass

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
        self.videocvs.create_image(0,0,image = self.photo, anchor = tk.NW)
      self.parent.after(delay, self.capture, delay)

  def place_on_grid (self, row, column, rowspan, columnspan):
    self.videocvs.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan)
    self.videolbl.grid(row=row-1, column=column, rowspan=1, columnspan=columnspan, sticky=S)

  def multithreaded_capture(self, delay=33, init_call=False):
    if init_call:
      self.videocount = 0
      self.thr = Thread(target=self.endo_video.get_frames, args=(True,))
      self.thr.start()
    
    try:
      cv2image = self.endo_video.viddeque[-1]
      tkimage = PIL.Image.fromarray(cv2.cvtColor(cv2image, cv2.COLOR_BGR2RGB))
      self.photo = PIL.ImageTk.PhotoImage(tkimage)
      if self.videocount == 0: 
        self.video = self.videocvs.create_image(0, 0, image=self.photo, anchor=tk.NW)
      else:
        self.videocvs.itemconfig(self.video, image=self.photo)
      if self.endo_video.stopflag or self.capture_stopflag:
        self.after (delay, self.videocap_ended)
      else:
        self.videocount += 1
        self.after (delay, self.multithreaded_capture, delay, False)
    except Exception:
      # time.sleep(20)
      # self.after (delay, self.multithreaded_capture, delay, False)
      result = None
      while result is None:
        try:
          result = "Passed"
          self.after (delay, self.multithreaded_capture, delay, False)
        except:
          result = None

  def videocap_ended(self):
    print ("Video capture ended.")

if __name__ == "__main__":
  aoavideo = CaptureVideoWEndoscope(0)
  aoavideo.show_video_standalone()