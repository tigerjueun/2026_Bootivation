from __future__ import annotations

import argparse,json,queue,sys,threading,time
from pathlib import Path
from typing import Any
import zmq
SRC=Path(__file__).resolve().parent/'src';sys.path.insert(0,str(SRC))
from bootivation_fusion.adapters.parsers import parse_pos_line,parse_vision_message
from bootivation_fusion.adapters.serial_worker import RiderSerialLink,SerialEventReader
from bootivation_fusion.config import load_config
from bootivation_fusion.core.state_manager import StateManager
from bootivation_fusion.domain.events import Event
from bootivation_fusion.event_logger import JsonlLogger
from ops_dashboard import OpsDashboard
RIDER_GAP=.30

def counts(v):v=v or {};return{n:max(0,int(v.get(n,0)))for n in('A','B','C')}
class PushLink:
 def __init__(self,endpoint,label):self.label=label;self.socket=zmq.Context.instance().socket(zmq.PUSH);self.socket.setsockopt(zmq.LINGER,0);self.socket.connect(endpoint);print(f'[{label}] PUSH {endpoint}')
 def send(self,p):self.socket.send_json(p);print(f'[{self.label}] {json.dumps(p,ensure_ascii=False)}')
 def close(self):self.socket.close(0)
class JsonSubscriber(threading.Thread):
 def __init__(self,endpoint,out,stop):super().__init__(daemon=True);self.endpoint=endpoint;self.out=out;self.stop=stop
 def run(self):
  s=zmq.Context.instance().socket(zmq.SUB);s.setsockopt_string(zmq.SUBSCRIBE,'');s.connect(self.endpoint);poll=zmq.Poller();poll.register(s,zmq.POLLIN);print(f'[rpi] SUB {self.endpoint}')
  try:
   while not self.stop.is_set():
    if s in dict(poll.poll(300)):
     m=s.recv_json()
     if isinstance(m,dict)and m.get('source')=='rpi_tray':self.out.put(m)
  finally:s.close(0)
class RetailSubscriber(threading.Thread):
 def __init__(self,endpoint,events,sessions,stop,dashboard,topic='retail'):super().__init__(daemon=True);self.endpoint=endpoint;self.events=events;self.sessions=sessions;self.stop=stop;self.dashboard=dashboard;self.topic=topic;self.cid=None;self.last={};self.loc={}
 def emit(self,raw):
  e=parse_vision_message(raw)
  if e:self.events.put(e);print(f'[vision] EVENT {raw}')
 def process(self,p):
  req={'timestamp','customer_id','active','visit_state','zone_A_picks','zone_B_picks','zone_C_picks','at_kiosk'}
  if req.difference(p):return
  c={'timestamp':float(p['timestamp']),'customer_id':int(p['customer_id']),'active':bool(p['active']),'visit_state':str(p['visit_state']),'zone_A_picks':max(0,int(p['zone_A_picks'])),'zone_B_picks':max(0,int(p['zone_B_picks'])),'zone_C_picks':max(0,int(p['zone_C_picks'])),'at_kiosk':bool(p['at_kiosk']),'event':p.get('event')};self.dashboard.update_vision(c);cid=c['customer_id'];cur={'A':c['zone_A_picks'],'B':c['zone_B_picks'],'C':c['zone_C_picks']}
  if not c['active']:
   if self.cid==cid:self.sessions.put({'kind':'CUSTOMER_EXIT','customer_id':cid,'picked':cur,'event':c.get('event'),'was_at_kiosk':self.loc.get(cid)=='POS'});self.emit('ENTER:EXIT');self.cid=None
   self.last.pop(cid,None);self.loc.pop(cid,None);return
  if self.cid is None:self.cid=cid;self.sessions.put({'kind':'CUSTOMER_STARTED','customer_id':cid})
  if cid!=self.cid:return
  prev=self.last.get(cid,{'A':0,'B':0,'C':0})
  for product in('A','B','C'):
   for _ in range(max(0,cur[product]-prev[product])):self.emit(f'REMOVE_CANDIDATE:{product}')
  self.last[cid]=cur;location='POS' if c['at_kiosk'] else str(c['visit_state']).upper();location={'ENTERING':'ENTRY','INSIDE':None,'ZONEA':'ZONE_A','ZONEB':'ZONE_B','ZONEC':'ZONE_C'}.get(location,location)
  if location and location!=self.loc.get(cid):self.emit(f'ENTER:{location}');self.loc[cid]=location;self.sessions.put({'kind':'CUSTOMER_AT_POS','customer_id':cid,'picked':cur}) if location=='POS' else None
 def run(self):
  s=zmq.Context.instance().socket(zmq.SUB);s.setsockopt_string(zmq.SUBSCRIBE,self.topic+' ');s.connect(self.endpoint);poll=zmq.Poller();poll.register(s,zmq.POLLIN);print(f'[vision] SUB {self.endpoint}')
  try:
   while not self.stop.is_set():
    if s not in dict(poll.poll(300)):continue
    try:t,b=s.recv_string().split(' ',1);self.process(json.loads(b)) if t==self.topic else None
    except(ValueError,json.JSONDecodeError):print('[vision] malformed')
  finally:s.close(0)
def send_rider(link,command):
 if link:link.send(command.strip());time.sleep(RIDER_GAP)
def console(events,orders,actions,stop):
 while not stop.is_set():
  try:l=input('fusion> ').strip()
  except EOFError:stop.set();return
  if not l:continue
  if l=='quit':stop.set();return
  if l=='reset':events.put(Event(source='manual',kind='SYSTEM_RESET'));continue
  if l in {'status','rpi','vision'}:actions.put({'action':l});continue
  if l.startswith('order '):
   order={}
   for token in l[6:].split(','):
    n,_,q=token.strip().partition('=')
    if n.upper()in{'A','B','C'}and q.isdigit():order[n.upper()]=int(q)
   if order:orders.put(order)
  elif l.startswith('event '):
   e=parse_vision_message(l[6:].strip());events.put(e) if e else None
  else:print('Unknown command')
def main():
 p=argparse.ArgumentParser();p.add_argument('--config',default='config/system.json');p.add_argument('--rpi-endpoint',default='tcp://10.77.0.2:5562');p.add_argument('--rpi-command-endpoint',default='tcp://10.77.0.2:5563');p.add_argument('--vision-evidence-endpoint');p.add_argument('--ui-host',default='127.0.0.1');p.add_argument('--ui-port',type=int,default=8088);a=p.parse_args();cfg=load_config(a.config);stop=threading.Event();events=queue.Queue();orders=queue.Queue();actions=queue.Queue();rpiq=queue.Queue();sessions=queue.Queue();sm=StateManager(cooldown_sec=float(cfg['remove_validation']['cooldown_sec']),rider_pick_source=str(cfg['rider'].get('pick_source','vision')));log=JsonlLogger(cfg['logging']['event_log']);ui=OpsDashboard(actions);ui.start(a.ui_host,a.ui_port);latest_rpi={};active=None;paid={};workers=[]
 if cfg['pos'].get('enabled'):w=SerialEventReader(name='pos',port=cfg['pos']['port'],baud=int(cfg['pos']['baud']),timeout=float(cfg['pos']['timeout_sec']),event_queue=events,parser=parse_pos_line);w.start();workers.append(w)
 rider=None
 if cfg['rider'].get('enabled'):
  try:rider=RiderSerialLink(cfg['rider']['port'],int(cfg['rider']['baud']),float(cfg['rider']['timeout_sec']));time.sleep(2)
  except Exception as e:print('[rider]',e)
 rsub=JsonSubscriber(a.rpi_endpoint,rpiq,stop);rsub.start();workers.append(rsub);rpush=PushLink(a.rpi_command_endpoint,'rpi');evidence=PushLink(a.vision_evidence_endpoint,'evidence')if a.vision_evidence_endpoint else None
 if cfg['vision'].get('enabled'):w=RetailSubscriber(cfg['vision']['subscriber_endpoint'],events,sessions,stop,ui,cfg['vision'].get('topic','retail'));w.start();workers.append(w)
 threading.Thread(target=console,args=(events,orders,actions,stop),daemon=True).start()
 try:
  while not stop.is_set():
   try:
    while True:m=rpiq.get_nowait();latest_rpi.clear();latest_rpi.update(m);ui.update_rpi(m)
   except queue.Empty:pass
   try:
    while True:
     s=sessions.get_nowait();cid=int(s['customer_id'])
     if s['kind']=='CUSTOMER_STARTED':active=cid;ui.customer_started(cid)
     elif s['kind']=='CUSTOMER_AT_POS':active=cid;ui.customer_at_pos(cid,s['picked'])
     else:
      result=ui.finalize_customer_exit(cid,s['picked'],paid.get(cid,{}),was_at_kiosk=bool(s.get('was_at_kiosk')),exit_event=s.get('event'))
      if result['severity']=='CRITICAL':send_rider(rider,'LED:RED');rpush.send({'command':'PLAY_AUDIO','event':'TRAY_MISMATCH'});evidence.send({'command':'CAPTURE_EVIDENCE','customer_id':cid,'reason':result['code'],'picked':s['picked'],'paid':paid.get(cid,{})}) if evidence else None
      paid.pop(cid,None);active=None
   except queue.Empty:pass
   try:
    while True:
     order=orders.get_nowait()
     for c in sm.set_order(order):send_rider(rider,c.command) if c.target=='rider' else None
   except queue.Empty:pass
   try:
    action=actions.get_nowait();name=action.get('action');print(json.dumps(sm.state.__dict__ if name=='status' else latest_rpi,ensure_ascii=False,indent=2))
   except queue.Empty:pass
   try:e=events.get(timeout=.2)
   except queue.Empty:ui.tick();continue
   before=bool(getattr(sm.state,'pos_payment_done',False));commands=sm.handle(e);ui.update_fusion(sm.state);log.write({'stage':'event',**e.to_dict()})
   for c in commands:send_rider(rider,c.command) if c.target=='rider' else None
   after=bool(getattr(sm.state,'pos_payment_done',False));mode=str(getattr(sm.state,'mode','')).upper()
   if not before and after and mode!='RIDER':
    expected=counts(getattr(sm.state,'pos_reported_items',{})or getattr(sm.state,'paid_items',{}));paid[active]=expected if active is not None else expected;ui.customer_paid(active,expected) if active is not None else None;rpush.send({'command':'PAYMENT_CONFIRMED','expected':expected})
   if e.kind=='SYSTEM_RESET':rpush.send({'command':'SYSTEM_RESET'})
   ui.tick()
 except KeyboardInterrupt:stop.set()
 finally:
  stop.set();[w.stop() for w in workers if hasattr(w,'stop')];rider.close() if rider else None;rpush.close();evidence.close() if evidence else None;ui.stop()
if __name__=='__main__':main()
