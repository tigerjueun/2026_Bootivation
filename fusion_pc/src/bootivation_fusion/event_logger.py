from __future__ import annotations
import json
from pathlib import Path
class JsonlLogger:
 def __init__(self,path):self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
 def write(self,record):
  with self.path.open('a',encoding='utf-8')as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
