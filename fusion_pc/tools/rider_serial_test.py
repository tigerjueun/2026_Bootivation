import argparse,serial
p=argparse.ArgumentParser();p.add_argument('--port',required=True);p.add_argument('--baud',type=int,default=9600);a=p.parse_args()
with serial.Serial(a.port,a.baud,timeout=.2)as d:
 while True:
  c=input('> ').strip()
  if c.lower()in{'quit','exit'}:break
  d.write((c+'\n').encode('ascii'));d.flush();print('TX',c)
