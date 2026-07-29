from __future__ import annotations
import argparse,time
from datetime import datetime
import cv2
from single_common import ROOT,GEOMETRY_PATH,capture_bgr,configure_camera,default_geometry,draw_tray,load_json,save_json
WINDOW='Single Camera - BEFORE/AFTER ROI';CONTROL='ROI Controls';selected='before';geometry=None
def noop(_):pass
def set_controls():
 g=geometry[selected]
 for n,k in [('LEFT','left'),('RIGHT','right'),('TOP','top'),('BOTTOM','bottom')]:cv2.setTrackbarPos(n,CONTROL,int(g[k]*1000))
def get_controls():
 l=cv2.getTrackbarPos('LEFT',CONTROL)/1000;r=cv2.getTrackbarPos('RIGHT',CONTROL)/1000;t=cv2.getTrackbarPos('TOP',CONTROL)/1000;b=cv2.getTrackbarPos('BOTTOM',CONTROL)/1000;return {'left':l,'right':max(r,l+.05),'top':t,'bottom':max(b,t+.05)}
def main():
 global selected,geometry
 p=argparse.ArgumentParser();p.add_argument('--layout',choices=['2x2','1x4'],default='2x2');args=p.parse_args();geometry=load_json(GEOMETRY_PATH,default_geometry());geometry['layout']=args.layout;cv2.namedWindow(WINDOW,cv2.WINDOW_NORMAL);cv2.namedWindow(CONTROL,cv2.WINDOW_NORMAL)
 for n in ('LEFT','RIGHT','TOP','BOTTOM'):cv2.createTrackbar(n,CONTROL,0,1000,noop)
 set_controls();cam=configure_camera();cam.start();time.sleep(1.5)
 try:
  while True:
   frame=capture_bgr(cam);geometry[selected]=get_controls();view=draw_tray(frame,'before',geometry);view=draw_tray(view,'after',geometry);cv2.imshow(WINDOW,view);key=cv2.waitKey(1)&0xFF
   if key in (ord('q'),27):break
   if key==ord('b'):selected='before';set_controls()
   elif key==ord('a'):selected='after';set_controls()
   elif key==ord('l'):geometry['layout']='1x4' if geometry['layout']=='2x2' else '2x2'
   elif key==ord('s'):save_json(GEOMETRY_PATH,geometry);d=ROOT/'captures';d.mkdir(parents=True,exist_ok=True);cv2.imwrite(str(d/(datetime.now().strftime('%Y%m%d_%H%M%S')+'_single_roi.jpg')),view)
 finally:
  try:cam.stop()
  except Exception:pass
  cam.close();cv2.destroyAllWindows()
if __name__=='__main__':main()
