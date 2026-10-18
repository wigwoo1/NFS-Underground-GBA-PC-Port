import csv,json,sys,ctypes as C,statistics,collections
from pathlib import Path
rp,tp,cp=map(Path,sys.argv[1:4]);cp.mkdir(exist_ok=True);r=json.loads(rp.read_text());rows=list(csv.DictReader(tp.open()));assert rows and {x['ProcessID'] for x in rows}=={'51264'}
f=C.c_int64();assert C.windll.kernel32.QueryPerformanceFrequency(C.byref(f));commits=[x['native_committed_sample'][6] for x in r['presentation_samples'] if x.get('native_committed_sample')];lo,hi=min(commits),max(commits)
pauses=[(x['native_pause_ack_ns'],x['native_resume_ack_ns']) for x in r['pause_events']]
shown=[];unshown=0
for x in rows:
 try:latency=float(x['DisplayLatency']);duration=float(x['DisplayedTime'])
 except ValueError:unshown+=1;continue
 if duration<=0:unshown+=1;continue
 start=int(x['CPUStartQPC'])*1000000000//f.value+int(latency*1000000);end=start+int(duration*1000000)
 if start<lo or end>hi or any(start<b and end>a for a,b in pauses):continue
 shown.append(dict(start_ns=start,displayed_ms=duration,cpu_start_qpc=int(x['CPUStartQPC']),display_latency_ms=latency))
assert shown
out=dict(result='OBSERVED_DISPLAY_TIMING',target_pid=51264,qpc_frequency=f.value,total_csv_rows=len(rows),displayed_nonpause_rows=len(shown),unshown_or_unavailable_rows=unshown,presentation_modes=dict(collections.Counter(x['PresentMode'] for x in rows)),displayed_duration_median_ms=statistics.median(x['displayed_ms'] for x in shown),displayed_duration_max_ms=max(x['displayed_ms'] for x in shown),displayed_over_two_refreshes=sum(x['displayed_ms']>1000/30 for x in shown),worst=sorted(shown,key=lambda x:x['displayed_ms'],reverse=True)[:10],scope='PresentMon compositor/display attribution for PID51264. QPC frequency converted; displayed durations limited to native commit range and exclude direct overlap with native pause acknowledgments. No exact scene/frame identity association; native pause to compositor latency can leave boundary artifacts. Preview640x480, not native4K display certification.')
(cp/'display-timing.json').write_text(json.dumps(out,indent=2));print(out)
