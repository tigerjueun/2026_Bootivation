from __future__ import annotations
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from bootivation_fusion.adapters.parsers import parse_pos_line,parse_vision_message
from bootivation_fusion.core.state_manager import StateManager
def feed(m,lines,parser):
 out=[]
 for line in lines:
  e=parser(line)
  if e:out.extend(m.handle(e))
 return out
class Tests(unittest.TestCase):
 def test_three_way(self):
  m=StateManager(cooldown_sec=0);m.set_order({'A':1,'B':1});feed(m,['REMOVE_CANDIDATE:A','REMOVE_CANDIDATE:B'],parse_vision_message);cmd=feed(m,['SESSION,START,ID=1','USER,RIDER','PAY:A','PAY:B','PAY_DONE','PAY_DONE,USER=RIDER,A=1,B=1,C=0,TOTAL=2,SESSION=1'],parse_pos_line);self.assertEqual(m.state.result,'PICKUP_COMPLETE');self.assertIn('LED:GREEN',[c.command for c in cmd])
 def test_wrong_pick(self):
  m=StateManager(cooldown_sec=0);m.set_order({'A':1});cmd=feed(m,['REMOVE_CANDIDATE:C'],parse_vision_message);self.assertIn('LED:RED',[c.command for c in cmd])
 def test_customer_no_double_count(self):
  m=StateManager();feed(m,['USER,CUSTOMER','PAY:A','PAY_DONE','PAY_DONE,USER=CUSTOMER,A=1,B=0,C=0,TOTAL=1,SESSION=1'],parse_pos_line);self.assertEqual(m.state.paid_items['A'],1)
if __name__=='__main__':unittest.main()
