"""Locate residual starvation in the frozen actual-function consuming-device replay.
No production edits, audio device, ROM or emulation required.
"""
from pathlib import Path
import csv,hashlib,json,os,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');parent=base/'NFSUG-pc-audio-partial-live-tests';out=base/'NFSUG-pc-audio-residual-analysis';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((parent/'partial-audio-component-report.json').read_text());assert proof['source_sha256']==sha(source/'live_host.c')
trace=base/'NFSUG-pc-audio-position-probe/audio-position-6000.csv';assert sha(trace)==proof['trace_sha256'];rows=list(csv.DictReader(trace.open()));events={};env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
old='fake_time=t;advance_driver();pending_samples=n;audio_drain(NULL);'
new=r"""double previous_time=fake_time,reserve=0;unsigned previous_queued=queued,ready=audio_count;for(unsigned k=0;k<queued;k++)reserve+=remaining[(head+k)%8];uint64_t event_before=audio_queue_empty_events;fake_time=t;advance_driver();pending_samples=n;audio_drain(NULL);if(audio_queue_empty_events>event_before)fprintf(stderr,"{\"time\":%.9f,\"interval_ms\":%.9f,\"previous_buffers\":%u,\"previous_reserve_frames\":%.9f,\"previous_ready_frames\":%u,\"newly_produced_frames\":%u,\"produced_after\":%llu,\"submitted_after\":%llu,\"pending_after\":%u,\"uncovered_before_service_ms\":%.9f}\n",t,(t-previous_time)*1000,previous_queued,reserve,ready,n,(unsigned long long)produced,(unsigned long long)submitted,audio_count,((t-previous_time)*44100-reserve)/44.1);"""
for mode in ['baseline','candidate']:
 c=parent/(mode+'-partial-simulation.c');s=c.read_text();actual=(source/'live_host.c').read_text() if mode=='candidate' else (parent/'before/live_host.c').read_text();a=actual.index('static void audio_drain(');b=actual.index('static int controller_check(',a);body=actual[a:b].strip();assert body in s;assert s.count(old)==1;s=s.replace(old,new);staged=out/(mode+'-residual.c');staged.write_text(s);exe=staged.with_suffix('.exe')
 subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror',str(staged),'-o',str(exe)],env=env,check=True)
 run=subprocess.run([str(exe),str(parent/'measured-service-times.txt')],env=env,check=True,capture_output=True,text=True);(out/(mode+'-stdout.json')).write_text(run.stdout);(out/(mode+'-events.jsonl')).write_text(run.stderr)
 summary=json.loads(run.stdout);assert summary==proof['rows'][mode]['measured'];events[mode]=[json.loads(line) for line in run.stderr.splitlines()];assert len(events[mode])==summary['empty_events']
 for e in events[mode]:
  matching=[(i,a,b) for i,(a,b) in enumerate(zip(rows[::2],rows[1::2])) if int(b['produced_frames'])==e['produced_after']];assert len(matching)==1
  index,a,b=matching[0];e['frame']=int(a['frame']);e['deadline_lag_ms']=float(a['deadline_lag_ms']);e['driver_trace_reported_reserve_frames']=int(a['remaining_frames']);e['baseline_device_trace_previous_service']=dict(rows[(index-1)*2+1]);e['production_trace_sha256']=sha(trace)
assert len(events['candidate'])==1
e=events['candidate'][0];e['all_previously_ready_pcm_ms']=e['previous_ready_frames']/44.1
e['would_immediate_prior_tail_cover_interval']=e['previous_reserve_frames']+e['previous_ready_frames']>=(e['interval_ms']*44.1)
report=dict(result='VERIFIED_RESIDUAL_AUDIO_SHORTAGE_LOCALIZED',events=events,source_unchanged_sha256=sha(source/'live_host.c'),component_receipt_sha256=sha(parent/'partial-audio-component-report.json'),script_sha256=sha(Path(__file__)),no_runtime_or_playable_change=True,limits='Ideal consuming queue with recorded producer service times; not WinMM audible gap duration. Future PCM is not available at prior service. Current-service PCM was generated during the elapsed core work, without earlier delivery evidence. No causal hardware-performance comparison.')
(out/'residual-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

