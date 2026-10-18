import sys,json,types,statistics,time,ctypes as C
from pathlib import Path
import owned_native_frame_join as candidate
baseline=types.ModuleType('baseline_join');baseline.__file__=candidate.__file__
exec(compile(Path(candidate.__file__).with_suffix('.py.before-direct-span-fill').read_text(),baseline.__file__,'exec'),baseline.__dict__)
checks=[];times={'baseline':[],'candidate':[]}
for count in (0,1,8,64,512,2048,4094):
 geometry=tuple(bytes([i%256])*(i%31) for i in range(count));header=b'header';base=b'prefixTAIL';expected=header+b''.join(geometry)+b'TAIL'
 for trial in range(12):
  order=[('baseline',baseline),('candidate',candidate)]
  if trial%2:order.reverse()
  for name,module in order:
   start=time.perf_counter_ns();out=module.join_frame(header,geometry,base,6);elapsed=time.perf_counter_ns()-start
   assert out==expected
   if count==2048:times[name].append(elapsed/1e6)
 checks.append(count)
for args in [(b'',(),b'',0),(b'x',(),b'a',2),(b'x',(bytearray(b'a'),),b'',0),(b'x',tuple(b'' for _ in range(4095)),b'',0)]:
 for module in (baseline,candidate):
  try:module.join_frame(*args)
  except ValueError:pass
  else:raise AssertionError('Invalid span accepted')
result=dict(result='PASS',span_counts=checks,exact_calls=168,invalid_inputs=4,median_2048_ms={k:statistics.median(v) for k,v in times.items()},scope='Alternating baseline/candidate immutable assembly, zero-length geometry spans and maximum4096totalspans; timing component only, no live cadence claim.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-dxgi-scene11413-20261007');(cp/'direct-span-component.json').write_text(json.dumps(result,indent=2));print(result)
