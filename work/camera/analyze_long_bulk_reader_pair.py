"""Compare complete native cadence and bounded wholecapture counters."""
import json,re,sys,statistics
from pathlib import Path
runs={}
for name,log_name in zip(('baseline','bulk'),sys.argv[1:3]):
 log=Path(log_name).read_text();raw=Path(re.findall(r'[^\r\n]*owned-native-\d+\.json',log)[0].strip());counts_path=Path(re.findall(r'EXACT_CAPTURE_WHOLE ([^\r\n]+)',log)[0].strip());r=json.loads(raw.read_text());t=json.loads(counts_path.read_text());a=r['bounded_diagnostic_stats']['whole_run_api_intervals'];ledger=a['native_commit_long_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records']);assert t['captures']==t['prepared']+t['fallback'];assert t['reader_parity_frames']==0 and t.get('reader_guard_checks',0)==0
 hud=[]
 for producer in r['producer_cycle_samples']:
  for read in producer['frame_read_boundaries']:
   p=read['exact_capture_profile'];s=p['reader_phase'];assert s[8:]==[p['epoch'],p['refresh']] and s[0]>0
   hud.append((s[4]-s[3])*1000/s[0])
 runs[name]=dict(raw=str(raw.resolve()),counts=str(counts_path.resolve()),native_intervals=a['native_commit_intervals'],long_records=ledger['total'],capture_total=t['captures'],capture_max_ms=t['max_call_ns']/1e6,capture_slow_total=t['slow_total'],capture_slow_retained=len(t['slow_retained']),recent_hud_samples=len(hud),recent_hud_median_ms=statistics.median(hud),recent_hud_max_ms=max(hud),prepared_pool_shutdown=r['frame_preparation_shutdown'])
out=dict(result='PASS_LONG_MATCHED_TIMING_AUDIT',runs=runs,scope='Sequential100s same settings fullscene originalclock, no parityreads. Complete native longledger/capturecounters, recentHUDsamples context only. Both require cadence qualification; averages and shortcleanwindows insufficient. No causal/exclusive scheduling or physicalscanout claim.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps({k:{'native':v['native_intervals'],'captures':v['capture_total'],'capture_max_ms':v['capture_max_ms'],'recent_hud_median_ms':v['recent_hud_median_ms']} for k,v in runs.items()},indent=2))
