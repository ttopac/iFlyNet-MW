from collections import deque
import cv2

import tkinter as tk
from tkinter import Tk, Frame, Canvas, Label
import PIL.Image, PIL.ImageTk
from threading import Thread
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

  def get_frame_for_TK (self, multithreaded=False): #Multithreaded is recommended for more than 1 camera
    if multithreaded:
      while True:
        if self.cap.isOpened():
          ret, frame = self.cap.read()
          resized = cv2.resize(frame, (self.new_w, self.new_h)) 
          if ret:
            self.viddeque.append(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
    else:
      if self.cap.isOpened():
        ret, frame = self.cap.read()
        resized = cv2.resize(frame, (self.new_w, self.new_h)) 
        if ret:
          return (ret, cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))

  def destroy_video_for_TK (self):
    if self.cap.isOpened():
      self.cap.release()


class DrawTKVideoCapture(Frame):
  def __init__(self, parent, window_title, camnum=0):
    Frame.__init__(self,parent)
    self.camnum = camnum
    self.parent = parent
    self.endo_video = CaptureVideoWEndoscope(self.camnum)
    # Create a canvas that can fit the above video source size
    self.videocan = Canvas(self.parent, width=self.endo_video.new_w, height=self.endo_video.new_h)
    self.videolbl = Label(self.parent, text=window_title)

  def update(self, delay=15):    
      ret, frame = self.endo_video.get_frame_for_TK()
      if ret:
        self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
        self.videocan.create_image(0, 0, image = self.photo, anchor = tk.NW)
      self.parent.after(delay, self.update, delay)

  def place_on_grid (self, row, column, rowspan, columnspan):
    self.videocan.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan)
    self.videolbl.grid(row=row-1, column=column, rowspan=1, columnspan=1)

  def multithreaded_capture(self, delay=15, init_call=False):
    if init_call:
      thr = Thread(target=self.endo_video.get_frame_for_TK, args=(True,))
      thr.daemon = True
      thr.start()
      time.sleep(0.1)

    self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(self.endo_video.viddeque[-1]))
    self.videocan.create_image(0, 0, image = self.photo, anchor = tk.NW)
    self.parent.after (delay, self.multithreaded_capture, delay)

if __name__ == "__main__":
  aoavideo = CaptureVideoWEndoscope(1)
  aoavideo.show_video_standalone()