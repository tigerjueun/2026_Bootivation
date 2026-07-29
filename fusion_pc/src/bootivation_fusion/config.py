from __future__ import annotations
import json
from pathlib import Path
def load_config(path):
 p=Path(path).resolve()
 with p.open('r',encoding='utf-8')as f:c=json.load(f)
 c['_config_path']=str(p);return c
