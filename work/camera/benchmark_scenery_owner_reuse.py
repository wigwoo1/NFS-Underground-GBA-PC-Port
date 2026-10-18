import sys,time,json,statistics
from pathlib import Path
sys.path.insert(0,'work/camera')
report='work/camera/prototype-runs/owned-native-1791351241812904600.json'
sys.argv=['setup',report,'0','unused'];ns={}
exec(compile(Path('work/camera/capture_fullscene_sample_oracle.py').read_text().split('import time,hashlib')[0],'setup','exec'),ns)
import owned_model_record_owners as current
old={};exec(compile(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/model-owner-phase-timing-20261007/owned_model_record_owners.py').read_text(),'reference','exec'),old)
from owned_prepared_world_motion import PreparedWorldMotion
rows=[]
try:
 ns['prepared'].close()
 for i in range(20):
  results={};times={}
  for label in (['reference','reuse'] if i%2==0 else ['reuse','reference']):
   p=PreparedWorldMotion(*ns['frames'],*ns['scenes'],ns['history'],ns['roads'],ns['rom'])
   try:
    fn=old['model_record_owners'] if label=='reference' else current.model_record_owners
    start=time.perf_counter_ns();mapping=fn(p.pair,ns['rom']);times[label]=time.perf_counter_ns()-start
    results[label]=dict(maps=[dict(x) for x in mapping],records=getattr(p.pair,'_scenery_record_pairs',{}),activation=getattr(p.pair,'_scenery_activation',{}),deactivation=getattr(p.pair,'_scenery_deactivation',{}))
   finally:p.close()
  assert results['reference']==results['reuse'];rows.append(times)
finally:ns['history'].close()
result=dict(result='PASS20_EXACT_COLD_OWNER_PAIRS',rows=rows,median_ms={k:statistics.median(x[k] for x in rows)/1e6 for k in ('reference','reuse')},scope='Alternating cold model ownership construction on fixed captured9107->9111; preparation constructor excluded, no live cadence proof.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/scenery-owner-reuse-benchmark-20261007');cp.mkdir(exist_ok=True);(cp/'benchmark.json').write_text(json.dumps(result,indent=2));print(result['median_ms'])
