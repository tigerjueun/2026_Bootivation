from __future__ import annotations

import time
import cv2
import numpy as np
from single_common import HSV_PATH,capture_bgr,configure_camera,default_hsv,load_json,save_json
WINDOW="Single Camera HSV"; CONTROL="HSV Controls"; selected_tray="before"; selected_product="A"; latest_hsv=None

def noop(_): pass

def create_controls():
 cv2.namedWindow(CONTROL,cv2.WINDOW_NORMAL); cv2.resizeWindow(CONTROL,520,320)
 for name,m in [("H MIN",179),("H MAX",179),("S MIN",255),("S MAX",255),("V MIN",255),("V MAX",255)]: cv2.createTrackbar(name,CONTROL,0,m,noop)

def set_controls(entry):
 lo,hi=entry["lower"],entry["upper"]
 for name,v in [("H MIN",lo[0]),("S MIN",lo[1]),("V MIN",lo[2]),("H MAX",hi[0]),("S MAX",hi[1]),("V MAX",hi[2])]: cv2.setTrackbarPos(name,CONTROL,int(v))

def get_controls():
 lo=[cv2.getTrackbarPos("H MIN",CONTROL),cv2.getTrackbarPos("S MIN",CONTROL),cv2.getTrackbarPos("V MIN",CONTROL)]; hi=[cv2.getTrackbarPos("H MAX",CONTROL),cv2.getTrackbarPos("S MAX",CONTROL),cv2.getTrackbarPos("V MAX",CONTROL)]; lo=[min(lo[i],hi[i]) for i in range(3)]; return {"lower":lo,"upper":hi}

def mouse_callback(event,x,y,flags,userdata):
 del flags,userdata
 global latest_hsv
 if event!=cv2.EVENT_LBUTTONDOWN or latest_hsv is None:return
 h,w=latest_hsv.shape[:2]
 if not(0<=x<w and 0<=y<h):return
 r=5; patch=latest_hsv[max(0,y-r):min(h,y+r+1),max(0,x-r):min(w,x+r+1)].reshape(-1,3); hv,sv,vv=np.median(patch,axis=0).astype(int); set_controls({"lower":[max(0,hv-10),max(0,sv-65),max(0,vv-65)],"upper":[min(179,hv+10),255,255]})

def main():
 global selected_tray,selected_product,latest_hsv
 hsv_data=load_json(HSV_PATH,default_hsv()); create_controls(); cv2.namedWindow(WINDOW,cv2.WINDOW_NORMAL); cv2.resizeWindow(WINDOW,1600,720); cv2.setMouseCallback(WINDOW,mouse_callback); set_controls(hsv_data[selected_tray][selected_product]); cam=configure_camera(); cam.start(); time.sleep(1.5)
 try:
  while True:
   frame=capture_bgr(cam); latest_hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV); entry=get_controls(); mask=cv2.inRange(latest_hsv,np.array(entry["lower"],np.uint8),np.array(entry["upper"],np.uint8)); result=cv2.bitwise_and(frame,frame,mask=mask); canvas=np.hstack((frame,cv2.cvtColor(mask,cv2.COLOR_GRAY2BGR),result)); cv2.imshow(WINDOW,canvas); key=cv2.waitKey(1)&0xFF
   if key in (ord('q'),27):break
   if key==ord('b'):selected_tray='before'
   elif key==ord('a'):selected_tray='after'
   elif key==ord('1'):selected_product='A'
   elif key==ord('2'):selected_product='B'
   elif key==ord('3'):selected_product='C'
   elif key==ord('s'):hsv_data[selected_tray][selected_product]=entry; save_json(HSV_PATH,hsv_data)
   if key in (ord('b'),ord('a'),ord('1'),ord('2'),ord('3')):set_controls(hsv_data[selected_tray][selected_product])
 finally:
  try:cam.stop()
  except Exception:pass
  cam.close(); cv2.destroyAllWindows()
if __name__=='__main__':main()
