"""Actual threaded held-scene dispatch with unchanged original tick ledger."""
from pathlib import Path
from project_paths import load_session
import ctypes as C,csv,json,os,subprocess,uuid,hashlib,re,math,statistics
p=Path(__file__).resolve().parent;source=p/'prototype-runs/threaded-prepared-4c0a478bbea14eedbc3a639513b0b9d6';session=load_session(Path(str(source)+'-session.json'));session['state']=str(p.parent/'race.state');state_hash=hashlib.sha256(Path(session['state']).read_bytes()).hexdigest();prefix=p/'prototype-runs'/('racing-motion-audit-'+uuid.uuid4().hex)
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')};env.update(NF_TEST_OCCURRENCE_NEGATIVE='1',NF_TEST_EXACT_QUERY_SAMPLE='1',NF_TEST_SAMPLED_ROOT_SELECTION='1',NF_TEST_PALETTE_EQUIVALENCE_NEGATIVE='1',NF_TEST_EQUIVALENT_WALL_PALETTES='1',NF_TEST_MODEL_TEXTURE_TRANSITION='1',NF_TEST_PREPARED_MOTION_CAPTURE='1',NF_TEST_MOTION_CAPTURE_PROFILE='1',NF_TEST_COMPLETE_STABLE_ONLY='1',NF_TEST_RACING_OWNED_CAPTURE='1',NF_TEST_THREADED_NEUTRAL='1',NF_LIVE_ROAD_ATTRIBUTES='1',NF_TEST_DISPLAY_PALETTE='1',NF_TEST_TRANSITION_DRAW_SCENE='1',NF_TEST_FOCAL_SAMPLE='1',NF_TEST_ORDERED_CAPTURE='1',NF_TEST_COMPLETE_ROAD_CACHE='1',NF_TEST_STABLE_CAPTURE='1',NF_TEST_NATIVE_BITMAP_TEXT='1',NF_CAPTURE_RETAINED_STRIP='1',NF_CAPTURE_INDEXED_COPY='1',NF_CAPTURE_WALL_OUTPUT_INDICES='1',NF_CAPTURE_MODEL_VIEWS='1',NF_TEST_INDEXED_ENTRANTS='1',NF_TEST_OWNED_ROOT_ENDPOINT='1',NF_TEST_THREADED_CAR_SELECTION='1',NF_THREADED_NO_READBACK='1',NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
for flag in ['NF_TEST_HUD_POOL_SHA256','NF_TEST_HUD_POOL_COST_PROFILE','NF_TEST_PRESENT_ATTEMPT_PROFILE','NF_TEST_HUD_POOL_SAMPLE_FILTER','NF_TEST_HUD_POOL_PLANES','NF_TEST_CLOCK_POLL_TRACE','NF_TEST_HUD_POOL_PREVIOUS_HINT','NF_VERIFY_OWNED_HUD_POOL','NF_TEST_OWNED_HUD_POOL','NF_TEST_HUD_ROW_POOL','NF_VERIFY_HUD_ROW_POOL','NF_TEST_GPU_TIMESTAMPS','NF_TEST_ABOVE_NORMAL_THREADS','NF_TEST_SURFACE_READ_REUSE','NF_VERIFY_SURFACE_READ_REUSE','NF_TEST_ASYNC_RENDER_FINISH','NF_TEST_DIRECT_CAPTURE_ROM','NF_TEST_VERIFY_CAPTURE_ROM','NF_TEST_CLOCK_BACKLOG_PROFILE','NF_TEST_WALL_SHADE_LOOKUP_CACHE','NF_TEST_SHARED_MOTION_CAPTURE','NF_TEST_SHARED_SOURCE_RETIRE_EACH_CAPTURE','NF_TEST_MOTION_OWNER_PROFILE','NF_TEST_DISTINCT_OCCURRENCE_GEOMETRY','NF_LAYER_DIRTY','NF_VERIFY_LAYER_DIRTY','NF_TEST_DIRECT_CAPTURE_RAM','NF_TEST_VERIFY_CAPTURE_RAM','NF_TEST_CAPTURE_EVENT_PROFILE','NF_TEST_THREAD_CPU_PROFILE','NF_TEST_SPLIT_STAGE_PROFILE','NF_TEST_SPLIT_PROFILE_SYNC','NF_TEST_PAGE_STAGE_PROFILE','NF_TEST_COMPLETE_CAPTURE_PROFILE']:
 if os.environ.get(flag)=='1':env[flag]='1'
if os.environ.get('NF_TEST_SPLIT_SCRATCH_REUSE')=='1':env['NF_TEST_SPLIT_SCRATCH_REUSE']='1'
if os.environ.get('NF_TEST_RACING_STEERING')=='1':env.pop('NF_TEST_THREADED_NEUTRAL',None);env['NF_THREADED_STEERING_ROUTE']='1'
readback=os.environ.get('NF_TEST_COMPLETE_READBACK')=='1'
if readback:env.pop('NF_THREADED_NO_READBACK',None);env['NF_TEST_COMPLETE_EXPORT']='1'
r=subprocess.run([str(p/'threaded-preview.exe'),str(p/'visibility-probe-wide.dll'),session['rom'],session['state'],str(prefix),os.environ.get('NF_TEST_RACING_SECONDS','4')],env=env,capture_output=True,text=True,timeout=50);Path(str(prefix)+'-host.log').write_text(r.stdout+r.stderr);print(r.stdout[-2500:]);print(r.stderr);assert r.returncode==0,r.returncode
draws=list(csv.DictReader(Path(str(prefix)+'-worker.csv').open()));stable=[x for x in draws if x.get('frame_kind')=='5'];print('worker columns',list(draws[0]) if draws else [],'stable',len(stable));assert draws and all(int(x['result'])==0 for x in draws);assert all(x['frame_kind'] in ('4','5','6') for x in draws);assert hashlib.sha256(Path(session['state']).read_bytes()).hexdigest()==state_hash
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint];assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
inputs=list(csv.DictReader(Path(str(prefix)+'-input.csv').open()))
if os.environ.get('NF_TEST_RACING_STEERING')=='1':
 assert all(int(row['keys'])==(1|(32 if 180<=int(row['index'])<500 else 16 if 500<=int(row['index'])<720 else 0)) for row in inputs)
steering_gate=os.environ.get('NF_TEST_RACING_STEERING')!='1' or {1,33,17}.issubset({int(row['keys']) for row in inputs})
try:
 for row in inputs:d.nf_frame(int(row['keys']))
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=Path(str(prefix)+'-baseline-'+name+'.bin');d.nf_dump(str(path).encode(),address,size);assert path.read_bytes()==Path(str(prefix)+'-'+name+'.bin').read_bytes()
finally:d.nf_close()
stats={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',r.stdout)}
if os.environ.get('NF_TEST_GPU_TIMESTAMPS')=='1':
 assert stats['gpu_timer_started']==stats['gpu_timer_resolved']==stats['rendered'] and stats['gpu_timer_started']>0 and stats['gpu_timer_pending']==0
if os.environ.get('NF_TEST_HUD_ROW_POOL')=='1':
 assert stats['hud_pool_draws']>0 and stats['hud_pool_stored_bytes']>0
 if os.environ.get('NF_VERIFY_HUD_ROW_POOL')=='1':assert stats['hud_pool_verified_rows']==160*stats['hud_pool_draws']
if os.environ.get('NF_TEST_OWNED_HUD_POOL')=='1':
 pool_records=re.findall(r'owned_hud_pool full_bytes=(\d+) stored_bytes=(\d+) epoch=(\d+)',r.stdout)
 assert pool_records and all(int(e)>0 and 0<int(b)<=int(a)+720 for a,b,e in pool_records)
if os.environ.get('NF_TEST_HUD_POOL_SHA256')=='1':
 assert os.environ.get('NF_TEST_OWNED_HUD_POOL')=='1' and os.environ.get('NF_TEST_HUD_POOL_PLANES')=='1'
 integrity_records=re.findall(r'owned_hud_pool full_bytes=\d+ stored_bytes=\d+ epoch=\d+ integrity=(\d+)',r.stdout)
 assert integrity_records and len(integrity_records)==len(pool_records) and all(int(x)==258 for x in integrity_records)
if os.environ.get('NF_VERIFY_OWNED_HUD_POOL')=='1':
 assert os.environ.get('NF_TEST_OWNED_HUD_POOL')=='1' and readback
 assert r.stdout.count('owned_hud_pool_pixels_exact=8294400 pool_epoch_negative=1 pool_payload_negative=1')==6
rate=16777216/(280896*60)
for row in draws:
 slot=(float(row['target'])-int(row['source_base'])+8)/rate;assert abs(slot-round(slot))<1e-7
cache_gate=stats['complete_road_cache_hits']>0
readback_gate=not readback or (stats['complete_motion_verified']==6 and stats['complete_ordered_verified']==6)
tick_ms=sorted((int(x['end_ns'])-int(x['start_ns']))/1e6 for x in inputs)
tick_budget_ms=280896/16777216*1000
tick_timing=dict(count=len(tick_ms),median_ms=statistics.median(tick_ms),p95_ms=tick_ms[int((len(tick_ms)-1)*.95)],max_ms=max(tick_ms),original_budget_ms=tick_budget_ms,over_budget=sum(x>tick_budget_ms for x in tick_ms),total_tick_ms=sum(tick_ms))
report=dict(steering_gate_passed=steering_gate,cache_gate_passed=cache_gate,readback_gate_passed=readback_gate,original_tick_timing=tick_timing,complete_readback_requested=readback,host_stats=stats,original_presentation_clock_grid_verified=True,result='MEASURED' if readback_gate and cache_gate and steering_gate else 'FAILED_REQUIRED_GATES',prefix=str(prefix),stable_worker_draws=len(stable),ordered_worker_draws=sum(x["frame_kind"]=="4" for x in draws),frame_kind_counts={k:sum(x["frame_kind"]==k for x in draws) for k in sorted(set(x["frame_kind"] for x in draws))},original_updates=len(inputs),original_ram_exact=True,scope='Actual racing queued worker held complete snapshots at unchanged fractional presentation targets; no smooth60fps gameplay proof');(p/'threaded-racing-motion-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


assert readback_gate, 'Required six motion and six ordered readbacks were not verified; failure evidence saved in report'
assert cache_gate, 'No road cache reuse observed; evidence retained'
assert steering_gate, 'Steering route coverage incomplete; state and timing evidence retained'











