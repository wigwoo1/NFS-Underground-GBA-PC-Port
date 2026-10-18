"""JSON encoding for diagnostic endpoint road records; no executable payloads."""
from dataclasses import fields
from owned_complete_road_candidates import RoadCandidate

def encode(value):
 if isinstance(value,bytes):return {'type':'bytes','hex':value.hex()}
 if isinstance(value,RoadCandidate):return {'type':'RoadCandidate','fields':{f.name:encode(getattr(value,f.name)) for f in fields(value)}}
 if isinstance(value,tuple):return {'type':'tuple','items':[encode(x) for x in value]}
 if isinstance(value,list):return {'type':'list','items':[encode(x) for x in value]}
 if isinstance(value,dict):
  if not all(isinstance(k,str) for k in value):raise ValueError('Invalid road diagnostic keys')
  return {'type':'dict','items':{k:encode(v) for k,v in value.items()}}
 if value is None or isinstance(value,(bool,int,float,str)):return value
 raise ValueError('Unsupported road diagnostic value '+type(value).__name__)

def decode(value):
 if not isinstance(value,dict):return value
 kind=value['type']
 if kind=='bytes':return bytes.fromhex(value['hex'])
 if kind=='RoadCandidate':return RoadCandidate(**{k:decode(v) for k,v in value['fields'].items()})
 if kind=='tuple':return tuple(decode(v) for v in value['items'])
 if kind=='list':return [decode(v) for v in value['items']]
 if kind=='dict':return {k:decode(v) for k,v in value['items'].items()}
 raise ValueError('Unsupported road diagnostic type')
