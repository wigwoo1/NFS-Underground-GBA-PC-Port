import ctypes as C,struct,json,time,statistics
from pathlib import Path
from owned_source_native_depth_rectangle_candidate import OwnedProjectionTable
values=list(struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]))
class Baseline:
 def __init__(self,values):
  self.values=tuple(values)
  if len(self.values)!=32768 or any(not isinstance(v,int) or not 0<=v<=0xffffffff for v in self.values):raise ValueError('Invalid projection table')
  self.native=(C.c_uint32*32768)(*self.values)
for cls in (Baseline,OwnedProjectionTable):
 v=list(values);table=cls(v);assert bytes(table.native)==struct.pack('<32768I',*values)
 v[100]^=123;assert table.values[100]==values[100] and table.native[100]==values[100]
 table.native[101]^=123;assert table.values[101]==values[101] and v[101]==values[101]
 for bad in (values[:-1],values+[0],[1.5]+values[1:],[-1]+values[1:],[0x100000000]+values[1:]):
  try:cls(bad)
  except ValueError:pass
  else:raise AssertionError('Invalid table accepted')
times={'baseline':[],'packed':[]}
for trial in range(30):
 for name,cls in ((('baseline',Baseline),('packed',OwnedProjectionTable)) if trial%2==0 else (('packed',OwnedProjectionTable),('baseline',Baseline))):
  begin=time.perf_counter_ns();t=cls(values);times[name].append((time.perf_counter_ns()-begin)/1e6)
result=dict(result='PASS',ownership='Caller mutation and native mutation do not alias snapshot tuple',invalid_cases_per_method=5,trials=30,median_ms={k:statistics.median(v) for k,v in times.items()},samples_ms=times,scope='Alternating isolated CPU construction with identical validation; not live rendering or scanout performance.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/projection-table-packing-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in result.items() if k!='samples_ms'}))
