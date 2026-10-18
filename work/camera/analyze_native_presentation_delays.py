"""Separate native deadline lateness, interpreter return and native commit spans.
CPU timestamps measure boundaries, not exclusive CPU, driver work or scanout.
"""
import json,sys
from pathlib import Path

def analyze(report):
 out=[]
 for r in report['presentation_samples']:
  w=r.get('native_wait_timing'); c=r.get('native_committed_sample')
  if not w or not c or not r.get('hidden_window_presented'):continue
  begin,deadline,returned,sleeps=w
  assert returned>=deadline and returned>=begin
  assert r['present_begin_ns']>=returned
  assert r['present_begin_ns']<=c[6]<=r['commit_return_ns']
  out.append(dict(display_index=r['display_index'],deadline_lateness_ms=(returned-deadline)/1e6,return_to_commit_begin_ms=(r['present_begin_ns']-returned)/1e6,commit_begin_to_native_completion_ms=(c[6]-r['present_begin_ns'])/1e6,native_completion_to_python_return_ms=(r['commit_return_ns']-c[6])/1e6,wait_started_late=begin>deadline))
 keys=('deadline_lateness_ms','return_to_commit_begin_ms','commit_begin_to_native_completion_ms','native_completion_to_python_return_ms')
 summary={k:dict(max_ms=max((x[k] for x in out),default=0),over_refresh=sum(x[k]>1000/60 for x in out)) for k in keys}
 return dict(scope='CPU boundary durations; lateness can include late arrival; no exclusive CPU or scanout proof',count=len(out),summary=summary,largest={k:sorted(out,key=lambda x:x[k],reverse=True)[:10] for k in keys})
if __name__=='__main__':
 p=Path(sys.argv[1]);a=analyze(json.loads(p.read_text()));p.with_suffix('.native-delays.json').write_text(json.dumps(a,indent=2));print(json.dumps(a['summary'],indent=2))
