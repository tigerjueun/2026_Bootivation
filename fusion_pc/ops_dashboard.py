from __future__ import annotations
import json,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from typing import Any
def counts(v):v=v or {};return{n:max(0,int(v.get(n,0)))for n in('A','B','C')}
class OpsDashboard:
 def __init__(self,action_queue):self.action_queue=action_queue;self.lock=threading.RLock();self.server=None;self.data={'fusion':{},'rpi':{},'vision':{},'customers':{},'alerts':[],'timeline':[]}
 def record_event(self,code,message,level='INFO',source='fusion',details=None):
  with self.lock:self.data['timeline']=(self.data['timeline']+[{'time':time.time(),'code':code,'message':message,'level':level,'source':source,'details':details or {}}])[-200:]
 def alert(self,code,message,severity='WARNING',details=None):
  with self.lock:self.data['alerts'].append({'id':f'{code}-{int(time.time()*1000)}','code':code,'message':message,'severity':severity,'details':details or {},'time':time.time(),'ack':False})
  self.record_event(code,message,severity,'alert',details)
 def update_fusion(self,state):
  with self.lock:self.data['fusion']=dict(getattr(state,'__dict__',{}))
 def update_rpi(self,m):
  with self.lock:self.data['rpi']=dict(m)
 def update_vision(self,c):
  with self.lock:self.data['vision']=dict(c);self.data['customers'][str(c['customer_id'])]=dict(c)
 def customer_started(self,cid):self.record_event('CUSTOMER_STARTED',f'customer {cid}')
 def customer_at_pos(self,cid,picked):self.record_event('CUSTOMER_AT_POS',f'customer {cid}',details={'picked':counts(picked)})
 def customer_paid(self,cid,paid):
  with self.lock:self.data['customers'].setdefault(str(cid),{})['paid']=counts(paid)
 def finalize_customer_exit(self,cid,picked,paid,was_at_kiosk=False,exit_event=None):
  picked,paid=counts(picked),counts(paid);unpaid={p:max(0,picked[p]-paid[p])for p in picked};overpaid={p:max(0,paid[p]-picked[p])for p in picked}
  if sum(picked.values())==0:code,severity='NO_ITEMS','INFO'
  elif sum(unpaid.values())>0:code='PARTIAL_PAYMENT' if sum(paid.values()) else('NO_PAYMENT' if was_at_kiosk else'BYPASS_POS_NO_PAYMENT');severity='CRITICAL'
  elif sum(overpaid.values())>0:code,severity='OVERPAYMENT','WARNING'
  else:code,severity='CLEARED','SUCCESS'
  result={'code':code,'severity':severity,'picked':picked,'paid':paid,'unpaid':unpaid,'overpaid':overpaid,'event':exit_event}
  self.alert(code,f'customer {cid}: {code}',severity,result) if severity in{'CRITICAL','WARNING'} else self.record_event(code,f'customer {cid}: {code}',severity,'customer',result);return result
 def system_reset(self):
  with self.lock:self.data['alerts'].clear();self.data['customers'].clear()
 def tick(self,*args,**kwargs):pass
 def configure_device(self,*args,**kwargs):pass
 def device_seen(self,*args,**kwargs):pass
 def customer_exit_pending(self,*args,**kwargs):pass
 def snapshot(self):
  with self.lock:return json.loads(json.dumps(self.data,default=str))
 def start(self,host='127.0.0.1',port=8088):
  d=self
  class H(BaseHTTPRequestHandler):
   def log_message(self,*_):pass
   def do_GET(self):
    if self.path=='/api/state':body=json.dumps(d.snapshot(),ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.end_headers();self.wfile.write(body);return
    body=b"<meta charset=utf-8><h1>Bootivation Operations</h1><pre id=s></pre><script>setInterval(async()=>s.textContent=JSON.stringify(await(await fetch('/api/state')).json(),null,2),700)</script>";self.send_response(200);self.end_headers();self.wfile.write(body)
  self.server=ThreadingHTTPServer((host,port),H);threading.Thread(target=self.server.serve_forever,daemon=True).start();print(f'[ui] http://{host}:{port}')
 def stop(self):
  if self.server:self.server.shutdown();self.server.server_close()
