"""Bounded recent diagnostic window; totals separate from retained records."""
from collections import deque
import json
class BoundedPresentationDiagnostics:
 def __init__(self,max_records=3600,max_bytes=16*1024*1024):
  if max_records<1 or max_bytes<1:raise ValueError('Positive retention limits required')
  self.max_records=max_records;self.max_bytes=max_bytes;self.records=deque();self.bytes=0;self.tail=None;self.total_records=0;self.dropped_records=0
 def __len__(self):return len(self.records)+(self.tail is not None)
 def append(self,row):
  encoded=json.dumps(row,separators=(',',':'),allow_nan=False).encode()
  if len(encoded)>self.max_bytes:raise ValueError('Diagnostic record exceeds retention byte limit')
  if self.tail is not None:
   previous=json.dumps(self.tail,separators=(',',':'),allow_nan=False).encode()
   if len(previous)>self.max_bytes:raise ValueError('Mutated diagnostic tail exceeds retention limit')
   self.records.append(previous);self.bytes+=len(previous)
  self.tail=row;self.total_records+=1
  while self.records and (len(self)>self.max_records or self.bytes+len(encoded)>self.max_bytes):
   self.bytes-=len(self.records.popleft());self.dropped_records+=1
 def __iter__(self):
  for row in self.records:yield json.loads(row)
  if self.tail is not None:yield self.tail
 def __reversed__(self):
  if self.tail is not None:yield self.tail
  for row in reversed(self.records):yield json.loads(row)
 def __getitem__(self,index):
  if index<0:index+=len(self)
  if not 0<=index<len(self):raise IndexError(index)
  return self.tail if index==len(self.records) else json.loads(self.records[index])
 def snapshot(self):return list(self)
 def stats(self):return dict(total_records=self.total_records,retained_records=len(self),dropped_records=self.dropped_records,completed_bytes=self.bytes,max_records=self.max_records,max_bytes=self.max_bytes,scope='Recent telemetry only; mutable tail counted at append. Not whole-run cadence evidence.')
