from __future__ import annotations
from dataclasses import dataclass,field
from time import time
from bootivation_fusion.domain.events import Event,OutputCommand
def item_counts():return{'A':0,'B':0,'C':0}
@dataclass
class FusionState:
 mode:str='IDLE';current_zone:str|None=None;removed_items:dict[str,int]=field(default_factory=item_counts);paid_items:dict[str,int]=field(default_factory=item_counts);order_items:dict[str,int]=field(default_factory=item_counts);rider_removed:dict[str,int]=field(default_factory=item_counts);rider_checked_items:dict[str,int]=field(default_factory=item_counts);inventory_removed_items:dict[str,int]=field(default_factory=item_counts);payment_batches:int=0;basket_status:str='UNKNOWN';result:str='IDLE';pos_boot_count:int=0;pos_session_id:int|None=None;pos_phase:str='UNKNOWN';pos_session_items:dict[str,int]=field(default_factory=item_counts);pos_reported_items:dict[str,int]=field(default_factory=item_counts);pos_reported_total:int=0;pos_payment_done:bool=False
class StateManager:
 def __init__(self,cooldown_sec=1.2,rider_pick_source='vision'):
  self.state=FusionState();self.cooldown_sec=cooldown_sec;self.rider_pick_source=rider_pick_source;self.last_remove=item_counts();self._committed=False;self._done=False
 def set_order(self,order):
  self.state.mode='RIDER';self.state.order_items=item_counts();self.state.rider_removed=item_counts();self.state.rider_checked_items=item_counts();self.state.result='RIDER_ORDER_READY'
  for i,q in order.items():
   if i in self.state.order_items:self.state.order_items[i]=max(0,int(q))
  n=self._next();return[OutputCommand('rider','LED:BLUE','order started'),OutputCommand('rider',f'SERVO:{n}','guide')]if n else[OutputCommand('rider','LED:RED','empty order')]
 def handle(self,e):
  c=[]
  if e.kind=='POS_BOOT':self.state.pos_boot_count+=1;self._reset_pos(None,'BOOT');self.state.result='POS_BOOTED';return c
  if e.kind=='POS_SESSION_START':self._rollback();self._reset_pos(e.payload.get('session_id'),'SESSION_START');return c
  if e.kind=='POS_RESET':self._rollback();self._reset_pos(self.state.pos_session_id,'SESSION_RESET');self.state.result='POS_SESSION_RESET';return c
  if e.kind=='POS_PHASE':self.state.pos_phase=str(e.payload.get('phase','UNKNOWN'));return c
  if e.kind=='MODE' and e.mode:self.state.mode=e.mode;self.state.result=f'{e.mode}_ACTIVE';return[OutputCommand('rider','LED:BLUE','rider POS')]if e.mode=='RIDER' else[]
  if e.kind=='ENTER' and e.zone:self.state.current_zone=e.zone;return c
  if e.kind=='EXIT' and e.zone:
   if self.state.current_zone==e.zone:self.state.current_zone=None
   return c
  if e.kind=='PAY' and e.item:return self._pos_pay(e.item,e.qty)
  if e.kind=='POS_COUNT':self.state.pos_reported_items=self._normal(e.payload.get('counts'));self.state.pos_reported_total=max(0,int(e.payload.get('total',sum(self.state.pos_reported_items.values()))));return c
  if e.kind=='PAY_DONE':self.state.pos_phase='DONE_SIGNAL';return self._commit(False)
  if e.kind=='POS_DONE_SUMMARY':
   if e.mode:self.state.mode=e.mode
   self.state.pos_session_id=e.payload.get('session_id',self.state.pos_session_id);summary=self._normal(e.payload.get('counts'));changed=self._reconcile(summary);self.state.pos_reported_items=summary;self.state.pos_reported_total=max(0,int(e.payload.get('total',sum(summary.values()))));self.state.pos_phase='DONE_SUMMARY';return self._commit(changed)
  if e.kind=='REMOVE_CANDIDATE' and e.item:
   now=time()
   if now-self.last_remove[e.item]<self.cooldown_sec:return c
   self.last_remove[e.item]=now;q=max(1,int(e.qty));self.state.inventory_removed_items[e.item]+=q
   if self.state.mode=='RIDER':self.state.rider_removed[e.item]+=q;return self._rider_pick(e.item)
   self.state.removed_items[e.item]+=q;return c
  if e.kind=='SYSTEM_RESET':self.state=FusionState();self.last_remove=item_counts();self._committed=False;self._done=False;return[OutputCommand('rider','RESET','reset')]
  return c
 def _pos_pay(self,item,qty):
  q=max(1,int(qty));self.state.pos_session_items[item]+=q
  if self.state.mode=='CUSTOMER':self.state.paid_items[item]+=q;return[]
  if self.state.mode=='RIDER':
   self.state.rider_checked_items[item]+=q
   if self.state.rider_checked_items[item]>self.state.order_items[item]:self.state.result=f'RIDER_POS_WRONG_ITEM:{item}';return[OutputCommand('rider','LED:RED','wrong POS item')]
   self.state.result='RIDER_POS_CHECKING';return[]
  return[]
 def _normal(self,raw):
  raw=raw or {};return{i:max(0,int(raw.get(i,0)))for i in('A','B','C')}
 def _reconcile(self,summary):
  ledger=self.state.paid_items if self.state.mode=='CUSTOMER' else(self.state.rider_checked_items if self.state.mode=='RIDER' else None);changed=False
  for i in('A','B','C'):
   d=summary[i]-self.state.pos_session_items[i]
   if d:
    changed=True
    if ledger is not None:ledger[i]=max(0,ledger[i]+d)
   self.state.pos_session_items[i]=summary[i]
  return changed
 def _rollback(self):
  if self._committed:return
  ledger=self.state.paid_items if self.state.mode=='CUSTOMER' else(self.state.rider_checked_items if self.state.mode=='RIDER' else None)
  if ledger:
   for i,q in self.state.pos_session_items.items():ledger[i]=max(0,ledger[i]-q)
 def _reset_pos(self,sid,phase):self.state.pos_session_id=sid;self.state.pos_phase=phase;self.state.pos_session_items=item_counts();self.state.pos_reported_items=item_counts();self.state.pos_reported_total=0;self.state.pos_payment_done=False;self._committed=False;self._done=False
 def _commit(self,force):
  first=not self._done;self.state.pos_payment_done=True;self._committed=True
  if first:self._done=True;self.state.payment_batches+=1 if self.state.mode=='CUSTOMER' else 0
  if self.state.mode=='CUSTOMER':self.state.result='CUSTOMER_PAYMENT_RECORDED';return[]
  if self.state.mode=='RIDER' and(first or force):return self._verify()
  return[]
 def _rider_pick(self,item):
  o,r=self.state.order_items,self.state.rider_removed
  if o.get(item,0)==0 or r[item]>o[item]:self.state.result=f'WRONG_PICKUP:{item}';return[OutputCommand('rider','LED:RED','wrong pickup')]
  if self._equal(r,o):self.state.result='RIDER_COLLECTED_WAIT_POS';return[OutputCommand('rider','LED:BLUE','go POS'),OutputCommand('rider','SERVO:HOME','go POS')]
  n=self._next();return[OutputCommand('rider','LED:BLUE','continue')]+([OutputCommand('rider',f'SERVO:{n}','next')]if n else[])
 def _verify(self):
  o,r,k=self.state.order_items,self.state.rider_removed,self.state.rider_checked_items
  if sum(o.values())==0:self.state.result='RIDER_DONE_NO_ORDER';return[OutputCommand('rider','LED:RED','no order')]
  if not self._equal(r,o):self.state.result='RIDER_REMOVAL_MISMATCH';return[OutputCommand('rider','LED:RED','vision mismatch')]
  if not self._equal(k,o):self.state.result='RIDER_POS_MISMATCH';return[OutputCommand('rider','LED:RED','POS mismatch')]
  self.state.result='PICKUP_COMPLETE';return[OutputCommand('rider','LED:GREEN','complete'),OutputCommand('rider','SERVO:HOME','complete')]
 @staticmethod
 def _equal(a,b):return all(a[i]==b[i]for i in('A','B','C'))
 def _next(self):
  return next((i for i in('A','B','C')if self.state.rider_removed[i]<self.state.order_items[i]),None)
