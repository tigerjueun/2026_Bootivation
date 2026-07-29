from __future__ import annotations

import json
from collections import Counter, deque
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from picamera2 import Picamera2

ROOT = Path.home() / "Bootivation" / "rpi_tray_single"
GEOMETRY_PATH = ROOT / "config" / "tray_geometry_single.json"
HSV_PATH = ROOT / "config" / "hsv_ranges_single.json"


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError): return default


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def default_geometry():
    return {"layout":"2x2","before":{"left":0.03,"right":0.48,"top":0.10,"bottom":0.90},"after":{"left":0.52,"right":0.97,"top":0.10,"bottom":0.90}}


def default_hsv():
    base={"A":{"lower":[5,100,70],"upper":[25,255,255]},"B":{"lower":[35,70,60],"upper":[85,255,255]},"C":{"lower":[90,70,60],"upper":[130,255,255]}}
    return {"before":json.loads(json.dumps(base)),"after":json.loads(json.dumps(base)),"classification":{"minimum_fill_ratio":{"A":0.16,"B":0.16,"C":0.16},"stable_frames":7,"morph_kernel":5}}


def configure_camera(index=0,width=1280,height=720,fps=15):
    cam=Picamera2(index)
    config=cam.create_video_configuration(main={"size":(width,height),"format":"RGB888"},raw=None,controls={"FrameRate":fps},buffer_count=2)
    cam.configure(config); return cam


def capture_bgr(camera): return camera.capture_array()


def make_slots(frame_shape,tray_geo,layout="2x2"):
    h,w=frame_shape[:2]; left=int(w*float(tray_geo["left"])); right=int(w*float(tray_geo["right"])); top=int(h*float(tray_geo["top"])); bottom=int(h*float(tray_geo["bottom"])); slots=[]
    if layout=="1x4":
        for c in range(4): slots.append((left+(right-left)*c//4,top,left+(right-left)*(c+1)//4,bottom))
    else:
        for r in range(2):
            for c in range(2): slots.append((left+(right-left)*c//2,top+(bottom-top)*r//2,left+(right-left)*(c+1)//2,top+(bottom-top)*(r+1)//2))
    return slots


def create_mask(frame_bgr,lower,upper,kernel_size):
    hsv=cv2.cvtColor(frame_bgr,cv2.COLOR_BGR2HSV); mask=cv2.inRange(hsv,np.array(lower,np.uint8),np.array(upper,np.uint8)); k=max(1,int(kernel_size)); k += 1 if k%2==0 else 0; kernel=np.ones((k,k),np.uint8); mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel,iterations=1); return cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel,iterations=2)


def classify_tray(frame_bgr,tray_name,geometry,hsv_data):
    slots=make_slots(frame_bgr.shape,geometry[tray_name],geometry.get("layout","2x2")); settings=hsv_data["classification"]; thresholds=settings["minimum_fill_ratio"]; masks={p:create_mask(frame_bgr,hsv_data[tray_name][p]["lower"],hsv_data[tray_name][p]["upper"],settings.get("morph_kernel",5)) for p in ("A","B","C")}; labels=[]; ratios_all=[]
    for x1,y1,x2,y2 in slots:
        mx=max(2,int((x2-x1)*0.08)); my=max(2,int((y2-y1)*0.08)); ratios={}
        for p,mask in masks.items():
            roi=mask[y1+my:y2-my,x1+mx:x2-mx]; ratios[p]=0.0 if roi.size==0 else float(np.count_nonzero(roi))/float(roi.size)
        best=max(ratios,key=ratios.get); labels.append(best if ratios[best]>=float(thresholds[best]) else "EMPTY"); ratios_all.append(ratios)
    return labels,ratios_all,{p:labels.count(p) for p in ("A","B","C","EMPTY")}


class StableCounts:
    def __init__(self,window_size): self.history={p:deque(maxlen=max(1,int(window_size))) for p in ("A","B","C","EMPTY")}
    def update(self,counts):
        result={}
        for p,hist in self.history.items():
            hist.append(int(counts[p])); c=Counter(hist); top=max(c.values()); candidates={v for v,n in c.items() if n==top}; result[p]=next((v for v in reversed(hist) if v in candidates),int(counts[p]))
        return result


def draw_tray(frame,tray_name,geometry,labels=None,ratios=None,counts=None):
    out=frame.copy(); slots=make_slots(out.shape,geometry[tray_name],geometry.get("layout","2x2")); title="BEFORE" if tray_name=="before" else "AFTER"
    for idx,(x1,y1,x2,y2) in enumerate(slots,1):
        cv2.rectangle(out,(x1,y1),(x2,y2),(255,255,255),2); text=f"{title}-{idx}"+(f":{labels[idx-1]}" if labels else ""); cv2.putText(out,text,(x1+5,y1+23),cv2.FONT_HERSHEY_SIMPLEX,0.55,(255,255,255),2,cv2.LINE_AA)
    if counts: cv2.putText(out,f"{title} A={counts['A']} B={counts['B']} C={counts['C']} E={counts['EMPTY']}",(10,28 if tray_name=="before" else 58),cv2.FONT_HERSHEY_SIMPLEX,0.63,(255,255,255),2,cv2.LINE_AA)
    return out
