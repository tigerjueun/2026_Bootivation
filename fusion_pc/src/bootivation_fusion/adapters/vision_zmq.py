from __future__ import annotations
import queue,threading,zmq
from bootivation_fusion.adapters.parsers import parse_vision_message
class VisionSubscriber(threading.Thread):
 def __init__(self,endpoint,event_queue,topic=''):super().__init__(name='vision-zmq',daemon=True);self.endpoint=endpoint;self.event_queue=event_queue;self.topic=topic;self.stop_event=threading.Event()
 def stop(self):self.stop_event.set()
 def run(self):
  s=zmq.Context.instance().socket(zmq.SUB);s.setsockopt_string(zmq.SUBSCRIBE,self.topic);s.setsockopt(zmq.RCVTIMEO,250);s.connect(self.endpoint)
  try:
   while not self.stop_event.is_set():
    try:m=s.recv_string()
    except zmq.Again:continue
    if self.topic and m.startswith(self.topic):m=m[len(self.topic):].lstrip()
    e=parse_vision_message(m);self.event_queue.put(e)if e else None
  finally:s.close(0)
