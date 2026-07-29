from __future__ import annotations
import json
from typing import Any
from bootivation_fusion.domain.events import Event
VALID_ITEMS={'A','B','C'};VALID_ZONES={'ENTRY','ZONE_A','ZONE_B','ZONE_C','POS','EXIT'};VALID_MODES={'CUSTOMER','RIDER'}
def integer(v,d=0):
 try:return int(v)
 except(TypeError,ValueError):return d
def fields(v):
 p=[x.strip()for x in v.split(',')];head=p[0].upper()if p else'';pos=[];out={}
 for x in p[1:]:
  if'='in x:k,val=x.split('=',1);out[k.strip().upper()]=val.strip()
  elif x:pos.append(x.upper())
 return head,pos,out
def item_counts(f):return{p:max(0,integer(f.get(p)))for p in VALID_ITEMS}
def parse_pos_line(line):
 v=line.strip()
 if not v:return None
 if v.startswith('EVENT:'):v=v.removeprefix('EVENT:').strip()
 if v.startswith('PAY_DONE,'):
  _,_,f=fields(v);mode=f.get('USER','').upper();c=item_counts(f);payload={'counts':c,'total':max(0,integer(f.get('TOTAL'),sum(c.values())))};sid=integer(f.get('SESSION'),-1)
  if sid>=0:payload['session_id']=sid
  return Event(source='pos',kind='POS_DONE_SUMMARY',mode=mode if mode in VALID_MODES else None,payload=payload)
 if v.startswith('PAY:'):
  item=v.partition(':')[2].upper();return Event(source='pos',kind='PAY',item=item)if item in VALID_ITEMS else None
 if v=='PAY_DONE':return Event(source='pos',kind='PAY_DONE')
 head,pos,f=fields(v)
 if head=='BOOT'and pos:return Event(source='pos',kind='POS_BOOT',payload={'firmware':pos[0]})
 if head=='SESSION'and pos and pos[0]=='START':return Event(source='pos',kind='POS_SESSION_START',payload={'session_id':integer(f.get('ID'),-1)})
 if v in{'SESSION_RESET','RESET'}:return Event(source='pos',kind='POS_RESET')
 if head=='USER'and pos and pos[0]in VALID_MODES:return Event(source='pos',kind='MODE',mode=pos[0])
 if head=='COUNT':
  c=item_counts(f);return Event(source='pos',kind='POS_COUNT',payload={'counts':c,'total':max(0,integer(f.get('TOTAL'),sum(c.values())))})
 if head=='EVT'and pos:return Event(source='pos',kind='POS_PHASE',payload={'phase':pos[0]})
 if v=='HELLO':return Event(source='pos',kind='POS_PHASE',payload={'phase':'HELLO'})
 if v.startswith('MODE:'):
  mode=v.partition(':')[2].upper();return Event(source='pos',kind='MODE',mode=mode)if mode in VALID_MODES else None
 return None
def parse_vision_message(message):
 v=message.strip()
 if not v:return None
 if v.startswith('{'):
  try:d=json.loads(v)
  except json.JSONDecodeError:return None
  kind=str(d.get('type')or d.get('event')or'').upper()
  if kind in{'ENTER','ZONE_ENTER','EXIT','ZONE_EXIT'}:
   zone=str(d.get('zone','')).upper();return Event(source='vision',kind='ENTER'if'ENTER'in kind else'EXIT',zone=zone,payload=d)if zone in VALID_ZONES else None
  if kind=='REMOVE_CANDIDATE':
   item=str(d.get('item')or d.get('product')or'').upper();return Event(source='vision',kind=kind,item=item,qty=max(1,integer(d.get('qty'),1)),payload=d)if item in VALID_ITEMS else None
 if v.startswith('ENTER:'):
  zone=v.partition(':')[2].upper();return Event(source='vision',kind='ENTER',zone=zone)if zone in VALID_ZONES else None
 if v.startswith('EXIT:'):
  zone=v.partition(':')[2].upper();return Event(source='vision',kind='EXIT',zone=zone)if zone in VALID_ZONES else None
 if v.startswith('REMOVE_CANDIDATE:'):
  item=v.rpartition(':')[2].upper();return Event(source='vision',kind='REMOVE_CANDIDATE',item=item)if item in VALID_ITEMS else None
 return None
