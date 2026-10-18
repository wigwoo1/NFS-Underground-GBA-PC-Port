"""Verify a recorded threaded launcher session without launching another game."""
from pathlib import Path
import ctypes as C,csv,hashlib,json,re,sys,statistics
manifest=Path(sys.argv[1]).resolve();out=manifest.with_name(manifest.stem+'-verification.json')
out.write_text(json.dumps(dict(result='RUNNING')))
try:
 s=json.loads(manifest.read_text(encoding='utf-8-sig'));assert s['status']=='HOST_COMPLETE' and s['exit_code']==0
 for name in ('rom','state'):assert hashlib.sha256(Path(s[name]).read_bytes()).hexdigest()==s[name+'_sha256'].lower()
 prefix=s['prefix'];log=Path(prefix+'-host.log').read_text(encoding='utf-8-sig')
 stats={key:int(value) for key,value in re.findall(r'(\w+)=(\d+)',log)}
 if 'presentation_lag_ns' in s:assert stats['presentation_lag_ns']==s['presentation_lag_ns']
 assert stats['result']==0 and stats['window_owner']==stats['consumer']!=stats['producer']
 if s.get('window_lifecycle'):
  resumes=re.findall(r'threaded_window_resume=(\d+) before=(\d+) after=(\d+) steps=(\d+) start_ns=(\d+) end_ns=(\d+)',log)
  assert len(resumes)==4 and stats['pauses']==4
  for flags,before,after,steps,start,end in resumes:assert before==after and int(end)-int(start)>=200000000
  assert 'threaded_actual_iconic=1 resume=0' in log and 'threaded_actual_iconic=0 resume=1' in log
  assert len(re.findall(r'threaded_actual_resize_ok=1',log))==2
 assert stats['submitted']==stats['rendered']+stats['stale']+stats['cancelled']+stats['retired_pending']+stats['discarded']
 rows=list(csv.DictReader(Path(prefix+'-input.csv').open()));draws=list(csv.DictReader(Path(prefix+'-worker.csv').open()))
 assert len(rows)==stats['original_steps'] and len(draws)==stats['rendered']+stats['stale']+stats['cancelled'] and rows
 if stats['input_enabled']:assert stats['input_polls']==len(rows)-40
 for i,row in enumerate(rows):
  if s.get('steering_route'):assert int(row['keys'])==(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0))
  assert int(row['index'])==i and int(row['after'])==int(row['before'])+1 and 0<=int(row['keys'])<=1023
  if i:assert row['before']==rows[i-1]['after']
  if stats['input_enabled'] and not int(row['focused']):assert int(row['keys'])==0
 for row in draws:
  assert int(row['result'])==0 and int(row['committed']) in (-2,0,1)
  slot=round((float(row['target'])-int(row['source_base'])+s.get('source_delay_refreshes',8))*280896*60/16777216)
  deadline=int(row['clock_origin'])+(slot*1000000000+59)//60+int(row['lag_ns'])
  if 'presentation_lag_ns' in s:assert int(row['lag_ns'])==s['presentation_lag_ns']
  if stats['scheduled']:assert int(row['deadline_ns'])==deadline
  if stats['scheduled'] and int(row['committed'])==1:assert int(row['end_ns'])>=deadline
 # Every worker target must be an exact original-rate display slot; continuity
 # is reported for all runs and required for timing-only uncut loss-free runs.
 target_gaps=[];previous_slot=None;previous_schedule=None
 for row in draws:
  raw=(float(row['target'])-int(row['source_base'])+s.get('source_delay_refreshes',8))*280896*60/16777216
  slot=round(raw);assert abs(raw-slot)<1e-6
  schedule=(row['epoch'],row['clock_origin'],row['source_base'])
  if schedule==previous_schedule:
   assert slot>previous_slot
   if slot!=previous_slot+1:target_gaps.append(dict(previous=previous_slot,current=slot,missing=slot-previous_slot-1))
  previous_slot=slot;previous_schedule=schedule
 if s.get('timing_only') and not any(stats[k] for k in ('queue_full','unavailable','skipped','stale','retired_pending','discarded','epoch_cuts','pauses')):assert not target_gaps
 d=C.CDLL(str(Path(__file__).resolve().parent.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
 assert d.nf_init(s['rom'].encode(),b'') and d.nf_state(s['state'].encode(),0)
 try:
  for row in rows:d.nf_frame(int(row['keys']))
  for name,base,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
   baseline=Path(prefix+'-replay-'+name+'.bin');d.nf_dump(str(baseline).encode(),base,n)
   assert baseline.read_bytes()==Path(prefix+'-'+name+'.bin').read_bytes()
 finally:d.nf_close()
 accepted=[row for row in draws if int(row['committed'])==1]
 intervals=[(int(b['end_ns'])-int(a['end_ns']))/1e6 for a,b in zip(accepted,accepted[1:])]
 report=dict(result='PASS',original_updates=len(rows),native_presentations=sum(int(row.get("frame_kind",1)) in (1,3) for row in accepted),split_native_presentations=sum(int(row.get("frame_kind",1))==3 for row in accepted),hardware_presentations=sum(int(row.get("frame_kind",1))==2 for row in accepted),target_slot_gaps=target_gaps,consecutive_worker_targets=not target_gaps,focused_updates=sum(int(row['focused'])!=0 for row in rows),connected_updates=sum(int(row['connected'])!=0 for row in rows),exact_original_ram=True,intervals_ms=None if not intervals else dict(median=statistics.median(intervals),maximum=max(intervals)),smooth_60fps_verified=False,physical_controller_verified=False,scope='Recorded inputs and complete original RAM replay, immutable frame deadline/queue accounting and worker window ownership. Focus/connection telemetry does not verify physical Xbox response, input latency or scanout.')
 out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
except BaseException as error:
 out.write_text(json.dumps(dict(result='FAIL',error=str(error)),indent=2));raise
