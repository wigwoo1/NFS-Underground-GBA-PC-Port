"""Lossless append-only diagnostic spool with bounded record buffers."""
import threading,json
from pathlib import Path
from owned_compact_diagnostics import CompactDiagnostics,CompactPresentationDiagnostics
class DiskRows:
 def __init__(self,path):
  self.path=Path(path);self.file=self.path.open('xb+');self.count=0;self.lock=threading.RLock()
 def __len__(self):return self.count
 def append(self,value):
  if not isinstance(value,bytes) or b'\n' in value or len(value)>1024*1024:raise ValueError('Unbounded diagnostic record')
  with self.lock:self.file.seek(0,2);self.file.write(value+b'\n');self.count+=1
 def __iter__(self):
  with self.lock:self.file.flush();count=self.count
  with self.path.open('rb') as f:
   for _ in range(count):
    line=f.readline(1024*1024+2)
    if not line.endswith(b'\n'):raise ValueError('Incomplete diagnostic spool')
    yield line[:-1]
 def __getitem__(self,index):
  if index<0:index+=len(self)
  if not 0<=index<len(self):raise IndexError(index)
  return next(row for i,row in enumerate(self) if i==index)
 def __reversed__(self):
  with self.lock:self.file.flush();end=self.file.seek(0,2)
  pending=b''
  with self.path.open('rb') as f:
   while end:
    start=max(0,end-65536);f.seek(start);pending=f.read(end-start)+pending;end=start
    lines=pending.split(b'\n');pending=lines[0]
    for line in reversed(lines[1:]):
     if line:yield line
    if len(pending)>1024*1024:raise ValueError('Unbounded diagnostic spool line')
   if pending:yield pending
 def close(self):
  with self.lock:self.file.flush();self.file.close()
class DiskDiagnostics(CompactDiagnostics):
 def __init__(self,path):super().__init__();self.records=DiskRows(path)
class DiskPresentationDiagnostics(CompactPresentationDiagnostics):
 def __init__(self,path):super().__init__();self.records=DiskRows(path)
