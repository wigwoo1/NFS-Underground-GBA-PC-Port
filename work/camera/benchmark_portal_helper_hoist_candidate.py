from pathlib import Path
import sys,time,json,statistics
sys.path.insert(0,str(Path('work/camera').resolve()))
env={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),env)
import owned_portal_traversal as original
from owned_portal_helper_hoist_candidate import traverse as candidate
baseline=original.traverse.__code__;optimized=candidate.__code__;rows=[]
for repeat in range(24):
 hashes={};timings={}
 for label,code in ([('baseline',baseline),('candidate',optimized)] if repeat%2==0 else [('candidate',optimized),('baseline',baseline)]):
  original.traverse.__code__=code;history,prepared=env['prepare']();packets=[]
  try:
   begin=time.perf_counter_ns();samples=env['ProgressiveSourceWorldSamples'](prepared,env['alphas'],on_sample=packets.append);elapsed=time.perf_counter_ns()-begin
   hashes[label]=[env['fingerprint'](p) for p in packets];timings[label]=elapsed;samples.close()
  finally:history.close()
 assert hashes['baseline']==hashes['candidate'];rows.append(timings)
original.traverse.__code__=baseline
out=dict(result='PASS_ALTERNATING_COMPLETE_SAMPLE_PORTAL_HOIST',pairs=len(rows),samples_per_run=6,median_ms={k:statistics.median(x[k] for x in rows)/1e6 for k in ['baseline','candidate']},rows=rows,scope='Full saved-fixture six-sample preparation with exact byte/arrays/masks/details equality. Preparation construction excluded. No live cadence improvement or default promotion.')
Path('outputs/nfsug-native-renderer/camera-research/portal-helper-hoist-benchmark-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],out['median_ms'])
