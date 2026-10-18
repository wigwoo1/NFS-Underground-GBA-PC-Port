import runpy,json,time,statistics
from pathlib import Path
import owned_source_process_sidecar_candidate as current
old=runpy.run_path('work/camera/owned_source_process_sidecar_candidate.py.before-keyless-validation')
s=Path('work/camera/test_precomputed_source_eight_samples.py').read_text();ns={};exec(s[:s.index(' import gc')]+'\nfinally: pass\n',ns)
owner=ns['cached'];identity=(ns['scenes'][0].graph.epoch,ns['scenes'][0].graph.refresh,ns['scenes'][1].graph.refresh);payload=old['encode'](owner,identity);assert current.encode(owner,identity)==payload
samples=dict(owner.samples);owner.close();ns['history'].close()
a=old['decode'](payload,samples,identity);b=current.decode(payload,samples,identity);assert a[0]==b[0]
for alpha in a[1]:
 x,y=a[1][alpha],b[1][alpha];assert bytes(x[0])==bytes(y[0]) and bytes(x[1])==bytes(y[1]) and x[2:]==y[2:]
times={'baseline':[],'keyless':[]}
for trial in range(24):
 for label,decoder in ([('baseline',old['decode']),('keyless',current.decode)] if trial%2==0 else [('keyless',current.decode),('baseline',old['decode'])]):
  start=time.perf_counter_ns();decoder(payload,samples,identity);times[label].append((time.perf_counter_ns()-start)/1e6)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-sidecar-keyless-validation-20261007')
(cp/'baseline-parity-cost.json').write_text(json.dumps(dict(result='PASS',samples=len(samples),median_ms={k:statistics.median(v) for k,v in times.items()},trials_ms=times,scope='Actual eight captured sample sidecar baseline byte parity after owner close; alternating component timings, not live cadence proof'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print({k:statistics.median(v) for k,v in times.items()})