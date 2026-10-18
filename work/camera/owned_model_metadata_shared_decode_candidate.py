"""Reuse exact-owner validated full metadata; no new cache or borrowed buffers."""
import owned_motion_pairs as full
import owned_model_key_records_candidate as model
original=model._decode_records
stats=dict(hits=0,misses=0)
def decode(frame,source_keys=True,decode_trace=None):
 if source_keys=='models' and (type(frame) is bytes or isinstance(frame,full.SegmentedFrame)) and decode_trace is None:
  for owner,header,rows in getattr(full._record_cache,'entries',()):
   if owner is frame:
    stats['hits']+=1
    return dict(refresh=header[0],epoch=header[1],ticks=header[2],records=[dict(kind=k,context=c,blocks=list(b),key=key if k==3 else None) for k,c,b,key in rows])
 stats['misses']+=1
 return original(frame,source_keys,decode_trace)
def install():model._decode_records=decode
def uninstall():model._decode_records=original
