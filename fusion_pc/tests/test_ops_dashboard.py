import queue,unittest
from ops_dashboard import OpsDashboard
class TestOps(unittest.TestCase):
 def test_unpaid(self):
  ops=OpsDashboard(queue.Queue());r=ops.finalize_customer_exit(1,{'A':2,'B':1,'C':0},{'A':1,'B':1,'C':0},was_at_kiosk=True);self.assertEqual(r['code'],'PARTIAL_PAYMENT');self.assertEqual(r['unpaid'],{'A':1,'B':0,'C':0})
 def test_cleared(self):
  ops=OpsDashboard(queue.Queue());r=ops.finalize_customer_exit(1,{'A':1,'B':1,'C':0},{'A':1,'B':1,'C':0},was_at_kiosk=True);self.assertEqual(r['code'],'CLEARED')
if __name__=='__main__':unittest.main()
