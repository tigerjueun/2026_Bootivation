from __future__ import annotations
import queue,time
from ops_dashboard import OpsDashboard
class DemoState:mode='RIDER';current_zone='ZONE_B';result='RIDER_ORDER_READY';order_items={'A':1,'B':2,'C':1};rider_removed={'A':1,'B':1,'C':0};rider_checked_items={'A':0,'B':0,'C':0}
ops=OpsDashboard(queue.Queue());ops.start('127.0.0.1',8088)
for n in ('pos','rider','rpi','vision'):ops.configure_device(n,configured=True,online=True,expect_stream=n in {'rpi','vision'},detail='demo');ops.device_seen(n,'demo')
ops.customer_started(100);ops.update_vision({'customer_id':100,'active':True,'visit_state':'inside','zone_A_picks':2,'zone_B_picks':1,'zone_C_picks':1,'at_kiosk':True});ops.customer_paid(100,{'A':1,'B':1,'C':0});ops.update_fusion(DemoState());print('http://127.0.0.1:8088')
try:
 while True:ops.tick(stream_stale_sec=9999);time.sleep(1)
except KeyboardInterrupt:ops.stop()
