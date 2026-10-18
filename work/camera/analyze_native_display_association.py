"""Validate PID and explore temporal associations; do not assume ETW frame identity."""
import csv,json,sys,ctypes as C,bisect,statistics,collections
from pathlib import Path
rp,tp,cfgp,op=map(Path,sys.argv[1:5]);r=json.loads(rp.read_text());cfg=json.loads(cfgp.read_text(encoding='utf-8-sig'));rows=list(csv.DictReader(tp.open()));pid=cfg['game_pid'];assert rows and {int(x['ProcessID']) for x in rows}=={pid}
f=C.c_int64();assert C.windll.kernel32.QueryPerformanceFrequency(C.byref(f))
samples=[x for x in r['presentation_samples'] if x.get('native_committed_sample')];ts=[x['native_committed_sample'][6] for x in samples];assert ts==sorted(ts)
latencies=[];associations=[];durations=[];drop=collections.Counter();ambiguous=0
pauses=[(x['native_pause_ack_ns'],x['native_resume_ack_ns']) for x in r['pause_events']]
for index,row in enumerate(rows):
 t=int(row['CPUStartQPC'])*1000000000//f.value;j=bisect.bisect_left(ts,t);near=range(max(0,j-2),min(len(ts),j+3));candidates=[]
 for k in near:
  s=samples[k];a=s['native_commit_stage_ns'][3];b=s['native_committed_sample'][6]
  if a-500000<=t<=b+500000:candidates.append(k)
 if len(candidates)!=1:ambiguous+=1
 else:
  k=candidates[0];associations.append(dict(csv_index=index,display_index=samples[k]['display_index'],etw_cpu_start_ns=t,commit_ns=ts[k],delta_ms=(t-ts[k])/1e6))
 try:lat=float(row['DisplayLatency']);d=float(row['DisplayedTime'])
 except ValueError:drop['unavailable']+=1;continue
 if d<=0:drop['nonpositive_display_duration']+=1;continue
 latencies.append(lat);start=t+int(lat*1e6);end=start+int(d*1e6)
 # Exclude startup/end and native pauses plus100ms margin explicitly, not a correctness gate.
 if start<ts[0]+100000000 or end>ts[-1]-100000000 or any(start<b+100000000 and end>a-100000000 for a,b in pauses):continue
 durations.append(d)
assert durations
out=dict(result='PID_VALIDATED_TEMPORAL_DIAGNOSTIC',pid=pid,csv_rows=len(rows),unique_near_present_intervals=len(associations),ambiguous_or_unmatched=ambiguous,unique_native_indices=len({x['display_index'] for x in associations}),drop_classification=dict(drop),display_latency_median_ms=statistics.median(latencies),display_duration_histogram_ms=dict(collections.Counter(round(x) for x in durations)),guarded_displayed_rows=len(durations),guarded_over_25ms=sum(x>25 for x in durations),guarded_max_ms=max(durations),associations=associations,scope='PID exact. CPUStartQPC versus native callback interval +/-0.5ms yields temporal candidates, not semantic ETW-to-native frame identity. Display-duration diagnostic excludes native pauses/start/end plus100ms to assess robustness; no invented pass threshold or physical4K claim.')
op.write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='associations'})
