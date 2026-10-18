import owned_exact_preparation_worker_install_candidate as install
import _owned_frame_capture_profile_candidate as extension
import _owned_frame_capture_release_candidate as baseline
import runpy,time,json,statistics
from pathlib import Path
saved=extension.capture;count=0;trials=[]
def capture(*args):
 global count
 count+=1
 if not 40<=count<64:return saved(*args)
 row=dict(capture=count);packets={};hit_before=install.service.hits
 for kind in ((0,1) if count%2==0 else (1,0)):
  begin=time.perf_counter_ns();packets[kind]=install.service.capture(*args) if kind else baseline.capture(*args);end=time.perf_counter_ns()
  row['service_ms' if kind else 'baseline_ms']=(end-begin)/1e6
 assert packets[0]==packets[1]
 row['hit']=install.service.hits>hit_before;row['bytes']=len(packets[0]);row['paired_delta_ms']=row['service_ms']-row['baseline_ms'];trials.append(row)
 return packets[1]
extension.capture=capture
try:
 runpy.run_path('work/camera/run_native_exact_preparation_lifecycle_candidate.py',run_name='__main__');assert len(trials)==24
finally:extension.capture=saved
summary=dict(result='PASS_MATCHED_VARIABLE_SOURCE_CAPTURE_PARITY',trials=trials,hits=sum(x['hit'] for x in trials),distinct_sizes=len(set(x['bytes'] for x in trials)),medians={k:statistics.median(x[k] for x in trials) for k in ('service_ms','baseline_ms','paired_delta_ms')},by_hit={str(hit):dict(count=len(subset),median_paired_delta_ms=statistics.median(x['paired_delta_ms'] for x in subset)) for hit in (True,False) if (subset:=[x for x in trials if x['hit']==hit])},scope='24consecutiveactualsourceframes alternatingreadorder/exactbytes, servicequery/fallback included, no readyprewait. Duplicatecaptures/cache/backgroundcompetition perturblivecadence; matchedcapturecost only, notwholegameimprovement/60fps.')
Path('work/camera/prototype-runs/matched-variable-source-20261009.json').write_text(json.dumps(summary,indent=2));print({k:v for k,v in summary.items() if k!='trials'})
