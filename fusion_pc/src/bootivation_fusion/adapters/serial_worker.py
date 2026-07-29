from __future__ import annotations
import queue,threading
from collections.abc import Callable
import serial
from bootivation_fusion.domain.events import Event
class SerialEventReader(threading.Thread):
 def __init__(self,*,name,port,baud,timeout,event_queue,parser):super().__init__(name=name,daemon=True);self.port=port;self.baud=baud;self.timeout=timeout;self.event_queue=event_queue;self.parser=parser;self.stop_event=threading.Event()
 def stop(self):self.stop_event.set()
 def run(self):
  while not self.stop_event.is_set():
   try:
    with serial.Serial(self.port,self.baud,timeout=self.timeout)as device:
     print(f'[{self.name}] connected {self.port} @ {self.baud}')
     while not self.stop_event.is_set():
      raw=device.readline()
      if not raw:continue
      line=raw.decode('utf-8',errors='replace').strip()
      if line:
       print(f'[{self.name}] RAW {line}');event=self.parser(line);self.event_queue.put(event)if event else None
   except serial.SerialException as e:print(f'[{self.name}] serial error: {e}');self.stop_event.wait(1)
class RiderSerialLink:
 def __init__(self,port,baud,timeout):self.device=serial.Serial(port,baud,timeout=timeout);self.lock=threading.Lock();print(f'[rider] connected {port} @ {baud}')
 def send(self,command):
  with self.lock:self.device.write((command.strip()+'\n').encode('ascii'));self.device.flush()
  print(f'[rider] TX {command}')
 def close(self):self.device.close()
