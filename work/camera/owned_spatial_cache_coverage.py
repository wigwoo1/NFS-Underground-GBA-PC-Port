"""Isolated bounded counters on unchanged spatial cache decisions."""
import threading
from pathlib import Path
import owned_spatial_decode_cache_candidate as base
records=[];lock=threading.Lock();local=threading.local()
def count(index):
 row=getattr(local,'counts',None)
 if row is None:
  row=[threading.get_ident(),0,0,0]
  with lock:
   if len(records)>=16:raise RuntimeError('Spatial coverage thread bound exceeded')
   records.append(row)
  local.counts=row
 row[index]+=1
source=Path(base.__file__).read_text().split('def install():')[0]
source=source.replace('return _original(self,graph)','count(3);return _original(self,graph)')
source=source.replace('entries.append(entries.pop(index));self.rows=dict(rows);return','count(1);entries.append(entries.pop(index));self.rows=dict(rows);return')
source=source.replace(' _original(self,graph)\n',' count(2);_original(self,graph)\n')
namespace=dict(count=count);exec(compile(source,'spatial_cache_coverage','exec'),namespace)
def install():namespace['SpatialDescriptors'].__init__=namespace['cached_init']
