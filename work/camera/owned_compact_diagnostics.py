"""Retain diagnostic JSON values without a live nested Python object graph."""
import json,time
class CompactDiagnostics:
 def __init__(self):self.records=[];self.bytes=0;self.serialization_ns=0;self.serialization_max_ns=0;self.serialization_cpu_ns=0
 def __len__(self):return len(self.records)
 def append(self,row):
  started=time.perf_counter_ns();cpu=time.thread_time_ns()
  encoded=json.dumps(row,separators=(',',':'),allow_nan=False).encode('utf-8')
  elapsed=time.perf_counter_ns()-started;cpu_elapsed=time.thread_time_ns()-cpu
  self.records.append(encoded);self.bytes+=len(encoded)
  self.serialization_ns+=elapsed;self.serialization_max_ns=max(self.serialization_max_ns,elapsed);self.serialization_cpu_ns+=cpu_elapsed
 def stats(self):return dict(records=len(self),bytes=self.bytes,serialization_total_ns=self.serialization_ns,serialization_max_ns=self.serialization_max_ns,serialization_thread_cpu_ns=self.serialization_cpu_ns)
 def snapshot(self):return [json.loads(row) for row in self.records]

class CompactPresentationDiagnostics(CompactDiagnostics):
 """One mutable latest record; older completed records remain losslessly encoded."""
 def __init__(self):super().__init__();self.tail=None
 def __len__(self):return len(self.records)+(self.tail is not None)
 def append(self,row):
  if self.tail is not None:super().append(self.tail)
  self.tail=row
 def __getitem__(self,index):
  if index<0:index+=len(self)
  if not 0<=index<len(self):raise IndexError(index)
  return self.tail if index==len(self.records) else json.loads(self.records[index])
 def __iter__(self):
  for row in self.records:yield json.loads(row)
  if self.tail is not None:yield self.tail
 def __reversed__(self):
  if self.tail is not None:yield self.tail
  for row in reversed(self.records):yield json.loads(row)
 def flush(self):
  if self.tail is not None:super().append(self.tail);self.tail=None
 def snapshot(self):return list(self)
