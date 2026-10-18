import ctypes as C,struct,json,time,statistics
from pathlib import Path
bits=[0,0x8000000000000000,0x7ff0000000000000,0xfff0000000000000,0x7ff8000000000001,1,0x3ff0000000000000]
raw=b''.join(struct.pack('<Q',bits[i%len(bits)]) for i in range(768));out=(C.c_double*768).from_buffer_copy(raw)
for n in range(129):
 a=tuple(out)[:n*6];b=tuple(out[:n*6]);assert struct.pack('<'+'d'*len(a),*a)==struct.pack('<'+'d'*len(b),*b)
results=[]
for n in (0,4,16,64,128):
 samples={'baseline':[],'slice':[]}
 for trial in range(20):
  for name in ('baseline','slice') if trial%2==0 else ('slice','baseline'):
   begin=time.perf_counter_ns()
   for repeat in range(1000):value=tuple(out)[:n*6] if name=='baseline' else tuple(out[:n*6])
   samples[name].append((time.perf_counter_ns()-begin)/1e6)
 results.append(dict(count=n,median_1000_ms={k:statistics.median(v) for k,v in samples.items()},samples=samples))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/road-output-slice-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',counts_checked=129,results=results,scope='Bit-exact conversions including signed zero, infinities, NaN payload and subnormal; conversion component benchmark only, not clipping/live throughput.'),indent=2))
for name in ('test_road_output_slice.py','owned_sampled_road_clip.py','owned_sampled_road_clip.before-output-slice.py'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
print([(x['count'],x['median_1000_ms']) for x in results])
