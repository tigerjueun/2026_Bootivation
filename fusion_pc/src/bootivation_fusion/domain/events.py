from __future__ import annotations
from dataclasses import asdict,dataclass,field
from time import time
from typing import Any
@dataclass(frozen=True)
class Event:
 source:str;kind:str;item:str|None=None;zone:str|None=None;mode:str|None=None;person_id:int|None=None;qty:int=1;confidence:float|None=None;payload:dict[str,Any]=field(default_factory=dict);received_at:float=field(default_factory=time)
 def to_dict(self):return asdict(self)
@dataclass(frozen=True)
class OutputCommand:
 target:str;command:str;reason:str
