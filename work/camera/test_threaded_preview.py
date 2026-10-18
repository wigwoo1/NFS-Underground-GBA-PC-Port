"""Independent GL/window owner with exact original input/RAM verification."""
from pathlib import Path
import ctypes as C,csv,hashlib,json,os,re,subprocess,sys,uuid,statistics,math
p=Path(__file__).resolve().parent
report_path=p/'threaded-preview-tests.json'
report_path.write_text(json.dumps(dict(result='RUNNING')))
def failure(kind,error,trace):
 report_path.write_text(json.dumps(dict(result='FAIL',error=str(error)),indent=2));sys.__excepthook__(kind,error,trace)
sys.excepthook=failure
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'driving.state'
hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
prefix=p/'prototype-runs'/('threaded-'+uuid.uuid4().hex)
seconds=int(sys.argv[1]) if len(sys.argv)>1 else 5
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
env.update(NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
epoch_cut='--epoch-cut' in sys.argv
pause='--pause' in sys.argv
window='--window' in sys.argv
actual_window='--actual-window' in sys.argv
assert not actual_window or window
if actual_window:env['NF_TEST_THREADED_ACTUAL_WINDOW']='1'
window_close='--window-close' in sys.argv
assert not window_close or window
if window_close:env['NF_TEST_THREADED_CLOSE']='1'
assert not (window and (pause or epoch_cut))
if window:env['NF_TEST_THREADED_WINDOW']='1'
assert not (pause and epoch_cut)
if pause:env['NF_TEST_THREADED_PAUSE']='1'
if epoch_cut:env['NF_TEST_THREADED_EPOCH']='1'
polling='--polling' in sys.argv
if polling:env['NF_THREADED_POLLING']='1'
arrival='--arrival' in sys.argv
no_readback='--no-readback' in sys.argv
if no_readback:env['NF_THREADED_NO_READBACK']='1'
else:env['NF_THREADED_EXPORT_FRAME']='1'
if arrival:env['NF_THREADED_ARRIVAL']='1'
input_test='--input-test' in sys.argv
controller_smoke='--controller-smoke' in sys.argv
assert not (input_test and controller_smoke)
if input_test:env['NF_TEST_THREADED_INPUT']='1'
if controller_smoke:env['NF_THREADED_CONTROLLER']='1'
r=subprocess.run([str(p/'threaded-preview.exe'),str(p/'visibility-probe-wide.dll'),str(rom),str(state),str(prefix),str(seconds)],env=env,capture_output=True,text=True,timeout=seconds+30)
Path(str(prefix)+'-host.log').write_text(r.stdout+r.stderr)
assert r.returncode==0,r.stdout+r.stderr
stats={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',r.stdout)}
assert stats['result']==0 and stats['window_owner']==stats['consumer']!=stats['producer']
assert stats['verified']==(0 if no_readback else 12) and stats['submitted']==stats['rendered']+stats['stale']+stats['cancelled']+stats['retired_pending']+stats['discarded'] and stats['rendered']>12
inputs=list(csv.DictReader(Path(str(prefix)+'-input.csv').open()));draws=list(csv.DictReader(Path(str(prefix)+'-worker.csv').open()))
assert len(inputs)==stats['original_steps'] and len(draws)==stats['rendered']+stats['stale']+stats['cancelled']
assert all(int(row['result'])==0 and int(row['end_ns'])>=int(row['start_ns']) for row in draws)
assert all(float(b['target'])>float(a['target']) for a,b in zip(draws,draws[1:]))
source_gaps=[(float(b['target'])-float(a['target']))/(16777216/(280896*60)) for a,b in zip(draws,draws[1:]) if a['epoch']==b['epoch']]
assert all(math.isclose(gap,round(gap),abs_tol=1e-7) and round(gap)>=1 for gap in source_gaps), 'Source clock differs from original rate'
overlap=sum(any(int(tick['start_ns'])<int(draw['draw_end_ns']) and int(tick['end_ns'])>int(draw['start_ns']) for draw in draws) for tick in inputs[40:])
assert overlap>0, 'No actual original update overlapped worker rendering'
if epoch_cut:
 assert stats['epoch_cuts']==1 and stats['stale']==1
 assert stats['retired_pending']==3 and stats['queue_full']>0
 assert stats['epoch_clears']==1
 stale=[row for row in draws if int(row['committed'])==0]
 assert len(stale)==1 and int(stale[0]['epoch'])<stats['cut_epoch'] and int(stale[0]['end_ns'])>=stats['cut_ns']
 assert any(int(row['committed'])==1 and int(row['epoch'])==stats['cut_epoch'] for row in draws)
 assert all(int(row['epoch'])>=stats['cut_epoch'] for row in draws if int(row['committed'])==1 and int(row['end_ns'])>=stats['cut_ns'])
else:assert stats['epoch_cuts']==0 and (pause or window or stats['stale']==0)
if pause:
 assert stats['pauses']==1 and stats['pause_before']==stats['pause_after']
 assert stats['pause_end_ns']-stats['pause_start_ns']>=200000000
 assert stats['pause_start_ns']<=stats['worker_pause_clear_ns']<=stats['pause_end_ns']
 assert len({row['clock_origin'] for row in draws})==2
 assert not any(stats['pause_start_ns']<int(row['start_ns'])<stats['pause_end_ns'] for row in inputs)
elif window:
 resumes=[tuple(map(int,m)) for m in re.findall(r'threaded_window_resume=(\d+) before=(\d+) after=(\d+) steps=(\d+) start_ns=(\d+) end_ns=(\d+)',r.stdout)]
 assert stats['pauses']==4 and [m[0] for m in resumes]==[1,2,4,8]
 for flags,before,after,steps,start,end in resumes:
  assert before==after and end-start>=200000000
  assert not any(start<int(row['start_ns'])<end for row in inputs)
 assert len({row['clock_origin'] for row in draws})==5
 transitions=[tuple(map(int,m)) for m in re.findall(r'threaded_window_flags=(\d+) event_ns=(\d+)',r.stdout)]
 assert [value for value,stamp in transitions]==[1,0,2,0,4,0,8,0]
 clears=list(map(int,re.findall(r'worker_pause_clear_ns=(\d+)',r.stdout)))
 if actual_window:
  assert re.findall(r'threaded_actual_iconic=(\d+) resume=(\d+)',r.stdout)==[('1','0'),('0','1')]
  sizes=[tuple(map(int,m)) for m in re.findall(r'threaded_actual_resize_ok=(\d+) width=(\d+) height=(\d+) resume=(\d+)',r.stdout)]
  assert len(sizes)==2 and sizes[0]==(1,640,480,0)
  # Windows may constrain the outer height to the desktop work area.
  assert sizes[1][0]==1 and sizes[1][1]==1280 and 480<sizes[1][2]<=720 and sizes[1][3]==1
  assert not any(transitions[4][1]<=int(row['end_ns'])<transitions[5][1] and int(row['committed'])==1 for row in draws)
  assert any(int(row['committed'])==1 and int(row['start_ns'])>resumes[2][-1] for row in draws)
  assert not any(transitions[2][1]<=int(row['end_ns'])<transitions[3][1] and int(row['committed'])==1 for row in draws)
  assert all(any(transitions[i*2][1]<=stamp<=resumes[i][-1] for stamp in clears) for i in (0,2,3))
  assert any(int(row['committed'])==1 and int(row['start_ns'])>resumes[1][-1] for row in draws)
 else:assert 4<=len(clears)<=4+int(window_close) and all(any(transitions[i*2][1]<=stamp<=resumes[i][-1] for stamp in clears) for i in range(4))
else:assert stats['pauses']==0
assert stats['window_quit']==int(window_close)
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
try:
 for i,row in enumerate(inputs):
  keys=int(row['keys']);assert int(row['index'])==i and int(row['after'])==int(row['before'])+1 and 0<=keys<=1023
  if input_test and i>=40:assert keys==[1,2,32,0,0,32,1,17][(i-40)%8]
  elif controller_smoke:assert int(row['focused'])==0 and keys==0
  else:assert keys==1
  d.nf_frame(int(row['keys']))
 for name,base,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  baseline=Path(str(prefix)+'-baseline-'+name+'.bin');d.nf_dump(str(baseline).encode(),base,n)
  assert baseline.read_bytes()==Path(str(prefix)+'-'+name+'.bin').read_bytes()
finally:d.nf_close()
assert hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
accepted=[row for row in draws if int(row['committed'])==1]
assert stats['scheduled']==int(not arrival)
for row in draws:
 slot=round((float(row['target'])-int(row['source_base'])+8)*280896*60/16777216)
 expected=int(row['clock_origin'])+(slot*1000000000+59)//60+int(row['lag_ns'])
 assert int(row['deadline_ns'])==(0 if arrival else expected)
 if not arrival and int(row['committed'])==1:assert int(row['end_ns'])>=expected
lateness=[(int(row['end_ns'])-int(row['deadline_ns']))/1e6 for row in accepted] if not arrival else []
intervals=[(int(b['end_ns'])-int(a['end_ns']))/1e6 for a,b in zip(accepted,accepted[1:])]
report=dict(result='PASS',stats=stats,seconds=seconds,original_updates_overlapping_worker_draw=overlap,final_original_ram_exact=True,rom_state_unchanged=True,worker_intervals_ms=dict(median=statistics.median(intervals),p95=sorted(intervals)[int(.95*(len(intervals)-1))],maximum=max(intervals)),worker_lateness_ms=None if arrival else dict(median=statistics.median(lateness),p95=sorted(lateness)[int(.95*(len(lateness)-1))],maximum=max(lateness),over_2ms=sum(value>2 for value in lateness)),private_prefix=str(prefix),scope='Concurrent original producer and exclusive worker-created window/GL consumer. Worker calculates exact60Hz deadlines from original source-clock samples with explicit16.666667ms presentation lag; arrival mode disables waits. Twelve full4K same-submission redraw checks and exact original RAM replay. Hidden integration; deadline/swap completion telemetry is not physical Xbox, scanout, input latency or smooth60fps proof.')
report['image_checks']=stats['verified']
report['readbacks_disabled']=no_readback
if no_readback:report['scope']=report['scope'].replace('Twelve full4K same-submission redraw checks and exact original RAM replay.', 'No image readback verification in this pacing run; exact original RAM replay retained.')
report_path.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
