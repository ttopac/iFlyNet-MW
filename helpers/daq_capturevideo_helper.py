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
          if ret:
            resized = cv2.resize(frame, (self.new_w, self.new_h))
            self.viddeque.append(resized)

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
  def __init__(self, parent, window_title, camnum=0, save_video=False, save_path=None, save_duration=None):
    Frame.__init__(self,parent)
    self.window_title = window_title
    self.camnum = camnum
    self.parent = parent
    self.save_video = save_video
    self.save_path = save_path
    self.save_duration = save_duration
    self.endo_video = CaptureVideoWEndoscope(self.camnum)
    # Create a canvas that can fit the above video source size
    self.videocvs = Canvas(self.parent, width=self.endo_video.new_w, height=self.endo_video.new_h)
    self.videolbl = Label(self.parent, text=window_title, font=("Helvetica", 18))

  def update(self, delay=15):    
      ret, frame = self.endo_video.get_frame_for_TK()
      if ret:
        self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
        self.videocvs.create_image(0,0,image = self.photo, anchor = tk.NW)
      self.parent.after(delay, self.update, delay)

  def place_on_grid (self, row, column, rowspan, columnspan):
    self.videocvs.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan)
    self.videolbl.grid(row=row-1, column=column, rowspan=1, columnspan=columnspan, sticky=S)

  def multithreaded_capture(self, delay=33, init_call=False):
    if init_call:
      self.videocount = 0
      if self.save_video:
        self.video_writer = cv2.VideoWriter(self.save_path+self.window_title+'.avi', cv2.VideoWriter_fourcc(*'XVID'), 30, self.endo_video.size)
      thr = Thread(target=self.endo_video.get_frame_for_TK, args=(True,))
      thr.start()
    try:
      cv2image = self.endo_video.viddeque[-1]
      if self.save_video:
        print (self.videocount)
        self.video_writer.write(cv2image)
        if self.videocount == 1: print("First frame recorded")
      else:
        tkimage = PIL.Image.fromarray(cv2.cvtColor(cv2image, cv2.COLOR_BGR2RGB))
        self.photo = PIL.ImageTk.PhotoImage(tkimage)
        self.videocvs.create_image(0, 0, image = self.photo, anchor = tk.NW)
      if self.videocount==delay*self.save_duration:
        self.video_writer.release()
        print ("Video created.")
        self.save_video = False
        self.parent.after (delay, self.multithreaded_capture, delay, False)
      self.videocount += 1
      self.parent.after (delay, self.multithreaded_capture, delay, False)
    except Exception as inst:
      print (inst)
      self.parent.after (delay, self.multithreaded_capture, delay, False)

if __name__ == "__main__":
  aoavideo = CaptureVideoWEndoscope(0)
  aoavideo.show_video_standalone()