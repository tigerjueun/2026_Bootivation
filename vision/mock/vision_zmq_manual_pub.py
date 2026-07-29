import argparse,time,zmq
p=argparse.ArgumentParser();p.add_argument('--bind',default='tcp://*:5555');a=p.parse_args();s=zmq.Context.instance().socket(zmq.PUB);s.bind(a.bind);time.sleep(1);print('[vision mock]',a.bind)
try:
 while True:
  item=input('A/B/C/q> ').strip().upper()
  if item=='Q':break
  if item in{'A','B','C'}:s.send_string(f'REMOVE_CANDIDATE:{item}')
finally:s.close(0)
