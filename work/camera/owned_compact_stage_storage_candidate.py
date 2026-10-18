"""Lossless storage of repeated scalar timing keys; reports retain original schema."""
KEY='$stage_v1'
FIELDS=('name','started_ns','completed_ns','wall_ns','thread_cycles')
def pack(value):
 if isinstance(value,list):return [pack(x) for x in value]
 if not isinstance(value,dict):return value
 assert KEY not in value
 if all(k in value for k in FIELDS) and value['completed_ns']==value['started_ns']+value['wall_ns']:
  extra={k:pack(v) for k,v in value.items() if k not in FIELDS}
  extra[KEY]=[value['name'],value['started_ns'],value['wall_ns'],value['thread_cycles']]
  return extra
 return {k:pack(v) for k,v in value.items()}
def unpack(value):
 if isinstance(value,list):return [unpack(x) for x in value]
 if not isinstance(value,dict):return value
 out={k:unpack(v) for k,v in value.items() if k!=KEY}
 if KEY in value:
  name,start,wall,cycles=value[KEY]
  out.update(name=name,started_ns=start,completed_ns=start+wall,wall_ns=wall,thread_cycles=cycles)
 return out
