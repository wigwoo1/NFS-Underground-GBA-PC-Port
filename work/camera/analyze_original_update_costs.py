"""Separate actual native game-frame interval from Python wrapper wall time."""
import json,sys,statistics
from pathlib import Path
def analyze(r):
 rows=[]
 for x in r['original_update_samples']:
  a,b=x['native_boundary'][:2];assert x['started_ns']<=a<=b<=x['completed_ns']
  wall=(x['completed_ns']-x['started_ns'])/1e6;native=(b-a)/1e6;outside=wall-native
  rows.append(dict(refresh=x['refresh'],wall_ms=wall,native_ms=native,outside_native_ms=outside,thread_cycles=x['thread_cycles'],capture_profile=x.get('capture_profile')))
 assert len(rows)==r['original_updates'] and rows
 return dict(result='BOUNDARIES_VERIFIED',updates=len(rows),native_median_ms=statistics.median(x['native_ms'] for x in rows),outside_median_ms=statistics.median(x['outside_native_ms'] for x in rows),native_over_original_step=sum(x['native_ms']>280896/16777216*1000 for x in rows),longest_wrapper=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:12],longest_native=sorted(rows,key=lambda x:x['native_ms'],reverse=True)[:12],scope='Native nf_frame boundaries and outer Python call interval; outside residual includes interpreter entry/exit and OS scheduling. Thread cycles do not establish wall utilization or sole GIL cause.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if not k.startswith('longest')}));print(json.dumps(out['longest_wrapper'][:2]))
