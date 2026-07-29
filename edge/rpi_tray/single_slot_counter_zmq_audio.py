from __future__ import annotations

import argparse
import json
import queue
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import zmq

from single_common import (
    GEOMETRY_PATH,
    HSV_PATH,
    ROOT,
    StableCounts,
    capture_bgr,
    classify_tray,
    configure_camera,
    default_geometry,
    default_hsv,
    draw_tray,
    load_json,
)

AUDIO_MAP={"SYSTEM_READY":"system_ready.wav","PLACE_BEFORE":"place_before.wav","SCAN_PRODUCT":"scan_product.wav","SCAN_COMPLETED":"scan_completed.wav","TRAY_MISMATCH":"tray_mismatch.wav","SYSTEM_RESET":"system_reset.wav"}; PRODUCTS=("A","B","C")

def normalize_product_counts(value): value=value or {}; return {p:max(0,int(value.get(p,0))) for p in PRODUCTS}
def normalize_tray_counts(value): value=value or {}; return {p:max(0,int(value.get(p,0))) for p in ("A","B","C","EMPTY")}

class AudioWorker(threading.Thread):
 def __init__(self,audio_dir):
  super().__init__(daemon=True); self.audio_dir=audio_dir; self.commands=queue.Queue(); self.stop_event=threading.Event(); self.last_event=None; self.player="pw-play" if shutil.which("pw-play") else ("aplay" if shutil.which("aplay") else None)
 def enqueue(self,event_name):
  event_name=event_name.strip().upper()
  if event_name in AUDIO_MAP:self.commands.put(event_name)
 def stop(self):self.stop_event.set();self.commands.put(None)
 def run(self):
  while not self.stop_event.is_set():
   try:event_name=self.commands.get(timeout=.3)
   except queue.Empty:continue
   if event_name is None:return
   path=self.audio_dir/AUDIO_MAP[event_name]
   if not path.exists() or self.player is None:continue
   command=[self.player,str(path)] if self.player=="pw-play" else [self.player,"-q",str(path)]; self.last_event=event_name; print(f"[audio] PLAY {event_name} -> {path.name}"); subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)

class TrayAudioSession:
 def __init__(self,audio,settle_sec,missing_timeout_sec):
  self.audio=audio; self.settle_sec=max(.5,settle_sec); self.missing_timeout_sec=max(self.settle_sec,missing_timeout_sec); self.expected=None; self.scan_announced=False; self.result_announced=False; self.result="WAIT_BEFORE"; self.last_after_signature=None; self.last_after_change_at=time.monotonic(); self.before_empty_since=None
 def startup(self):self.audio.enqueue("SYSTEM_READY");self.audio.enqueue("PLACE_BEFORE")
 def reset(self):
  self.expected=None;self.scan_announced=False;self.result_announced=False;self.result="WAIT_BEFORE";self.last_after_signature=None;self.last_after_change_at=time.monotonic();self.before_empty_since=None;self.audio.enqueue("SYSTEM_RESET");self.audio.enqueue("PLACE_BEFORE")
 def payment_confirmed(self,expected):
  normalized=normalize_product_counts(expected)
  if sum(normalized.values())<=0:return
  self.expected=normalized;self.result_announced=False;self.result="WAIT_TRANSFER";self.before_empty_since=None;self.last_after_change_at=time.monotonic();self.audio.enqueue("SCAN_COMPLETED")
 def update(self,before,after):
  now=time.monotonic();bp=normalize_product_counts(before);ap=normalize_product_counts(after);bt=sum(bp.values());at=sum(ap.values())
  if self.expected is None and bt>0 and not self.scan_announced:self.scan_announced=True;self.result="SCANNING";self.audio.enqueue("SCAN_PRODUCT")
  signature=tuple(ap[p] for p in PRODUCTS)
  if signature!=self.last_after_signature:self.last_after_signature=signature;self.last_after_change_at=now
  if self.expected is None or self.result_announced:return
  if bt==0:
   if self.before_empty_since is None:self.before_empty_since=now
  else:self.before_empty_since=None;return
  if at<=0:return
  stable=now-self.last_after_change_at; empty=0 if self.before_empty_since is None else now-self.before_empty_since; expected_total=sum(self.expected.values())
  if at==expected_total and stable>=self.settle_sec:
   self.result="TRAY_COMPLETE" if ap==self.expected else "TRAY_MISMATCH"; self.result_announced=True
   if self.result=="TRAY_MISMATCH":self.audio.enqueue("TRAY_MISMATCH")
  elif empty>=self.missing_timeout_sec and stable>=self.settle_sec:self.result="TRAY_MISMATCH";self.result_announced=True;self.audio.enqueue("TRAY_MISMATCH")

def resolve_audio_dir(argument):
 candidates=([Path(argument).expanduser()] if argument else [])+[ROOT/"audio"/"wav",Path.home()/"Bootivation"/"rpi_tray"/"audio"/"wav",Path.home()/"Bootivation"/"rpi_tray_single"/"audio"/"wav"]
 return next((p for p in candidates if p.exists()),candidates[0])

def main():
 parser=argparse.ArgumentParser();parser.add_argument("--bind",default="tcp://*:5562");parser.add_argument("--command-bind",default="tcp://*:5563");parser.add_argument("--publish-interval",type=float,default=.8);parser.add_argument("--audio-dir");parser.add_argument("--settle-sec",type=float,default=1.8);parser.add_argument("--mismatch-timeout",type=float,default=7.0);parser.add_argument("--no-display",action="store_true");args=parser.parse_args();geometry=load_json(GEOMETRY_PATH,default_geometry());hsv=load_json(HSV_PATH,default_hsv());stable=int(hsv["classification"].get("stable_frames",7));sb=StableCounts(stable);sa=StableCounts(stable);log_dir=ROOT/"logs";cap=ROOT/"captures";log_dir.mkdir(parents=True,exist_ok=True);cap.mkdir(parents=True,exist_ok=True);ctx=zmq.Context.instance();pub=ctx.socket(zmq.PUB);pub.setsockopt(zmq.LINGER,0);pub.bind(args.bind);pull=ctx.socket(zmq.PULL);pull.setsockopt(zmq.LINGER,0);pull.bind(args.command_bind);audio=AudioWorker(resolve_audio_dir(args.audio_dir));audio.start();session=TrayAudioSession(audio,args.settle_sec,args.mismatch_timeout);cam=configure_camera();cam.start();time.sleep(1.5);session.startup();seq=0;last=0.;previous=None
 try:
  while True:
   while True:
    try:cmd=pull.recv_json(flags=zmq.NOBLOCK)
    except zmq.Again:break
    name=str(cmd.get("command","")).upper()
    if name=="SYSTEM_RESET":session.reset()
    elif name=="PAYMENT_CONFIRMED":session.payment_confirmed(cmd.get("expected",{}))
    elif name=="PLAY_AUDIO":audio.enqueue(str(cmd.get("event","")).upper())
   frame=capture_bgr(cam);bl,br,b0=classify_tray(frame,"before",geometry,hsv);al,ar,a0=classify_tray(frame,"after",geometry,hsv);bc=normalize_tray_counts(sb.update(b0));ac=normalize_tray_counts(sa.update(a0));session.update(bc,ac);signature=(tuple(bc.items()),tuple(ac.items()),tuple(bl),tuple(al),session.result,audio.last_event);now=time.monotonic()
   if signature!=previous or now-last>=max(.2,args.publish_interval):
    seq+=1;payload={"version":"1.1","source":"rpi_tray","event":"TRAY_COUNT","timestamp_ms":int(time.time()*1000),"sequence":seq,"layout":geometry.get("layout","2x2"),"before":bc,"after":ac,"before_slots":bl,"after_slots":al,"audio_state":{"last_audio":audio.last_event,"result":session.result,"expected":session.expected}};pub.send_json(payload);last=now;previous=signature
   if args.no_display:continue
   view=draw_tray(frame,"before",geometry,bl,br,bc);view=draw_tray(view,"after",geometry,al,ar,ac);cv2.imshow("Single Camera Tray + ZMQ + Audio",view);key=cv2.waitKey(1)&0xFF
   if key in (ord('q'),27):break
   if key==ord('s'):cv2.imwrite(str(cap/(datetime.now().strftime('%Y%m%d_%H%M%S')+'_zmq_audio.jpg')),view)
 except KeyboardInterrupt:pass
 finally:
  try:cam.stop()
  except Exception:pass
  cam.close();audio.stop();audio.join(timeout=2);pub.close(0);pull.close(0);cv2.destroyAllWindows()
if __name__=='__main__':main()
