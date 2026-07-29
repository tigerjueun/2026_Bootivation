from __future__ import annotations
import json,time
from datetime import datetime
import cv2
from single_common import GEOMETRY_PATH,HSV_PATH,ROOT,StableCounts,capture_bgr,classify_tray,configure_camera,default_geometry,default_hsv,draw_tray,load_json

def main():
 geometry=load_json(GEOMETRY_PATH,default_geometry()); hsv_data=load_json(HSV_PATH,default_hsv()); window=int(hsv_data['classification'].get('stable_frames',7)); sb=StableCounts(window); sa=StableCounts(window); log_dir=ROOT/'logs'; cap=ROOT/'captures'; log_dir.mkdir(parents=True,exist_ok=True); cap.mkdir(parents=True,exist_ok=True); cam=configure_camera(); cam.start(); time.sleep(1.5); previous=None
 try:
  while True:
   frame=capture_bgr(cam); bl,br,bc0=classify_tray(frame,'before',geometry,hsv_data); al,ar,ac0=classify_tray(frame,'after',geometry,hsv_data); bc=sb.update(bc0); ac=sa.update(ac0); payload={'timestamp_ms':int(time.time()*1000),'event':'TRAY_COUNT','before':bc,'after':ac,'before_slots':bl,'after_slots':al}; key_state=(tuple(bc.items()),tuple(ac.items()),tuple(bl),tuple(al))
   if key_state!=previous:
    print(json.dumps(payload,ensure_ascii=False)); (log_dir/'slot_counts.jsonl').open('a',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False)+'\n'); previous=key_state
   view=draw_tray(frame,'before',geometry,bl,br,bc); view=draw_tray(view,'after',geometry,al,ar,ac); cv2.imshow('Single Camera 2-Tray Counter',view); key=cv2.waitKey(1)&0xFF
   if key in (ord('q'),27):break
   if key==ord('s'):cv2.imwrite(str(cap/(datetime.now().strftime('%Y%m%d_%H%M%S')+'_single_count.jpg')),view)
 finally:
  try:cam.stop()
  except Exception:pass
  cam.close(); cv2.destroyAllWindows()
if __name__=='__main__':main()
