"""Actual threaded held-scene dispatch with unchanged original tick ledger."""
from pathlib import Path
from project_paths import load_session
import ctypes as C,csv,json,os,subprocess,uuid,hashlib,re,math
p=Path(__file__).resolve().parent;source=p/'prototype-runs/threaded-prepared-4c0a478bbea14eedbc3a639513b0b9d6';session=load_session(Path(str(source)+'-session.json'));prefix=p/'prototype-runs'/('motion-complete-'+uuid.uuid4().hex)
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')};env.update(NF_TEST_THREADED_NEUTRAL='1',NF_LIVE_ROAD_ATTRIBUTES='1',NF_TEST_DISPLAY_PALETTE='1',NF_TEST_TRANSITION_DRAW_SCENE='1',NF_TEST_FOCAL_SAMPLE='1',NF_TEST_ORDERED_CAPTURE='1',NF_TEST_COMPLETE_ROAD_CACHE='1',NF_TEST_PREPARED_MOTION_CAPTURE='1',NF_TEST_STABLE_CAPTURE='1',NF_TEST_NATIVE_BITMAP_TEXT='1',NF_CAPTURE_RETAINED_STRIP='1',NF_CAPTURE_INDEXED_COPY='1',NF_CAPTURE_WALL_OUTPUT_INDICES='1',NF_CAPTURE_MODEL_VIEWS='1',NF_TEST_INDEXED_ENTRANTS='1',NF_TEST_OWNED_ROOT_ENDPOINT='1',NF_TEST_THREADED_CAR_SELECTION='1',NF_THREADED_NO_READBACK='1',NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
for flag in ['NF_TEST_SURFACE_COMMAND_REUSE_VERIFY','NF_TEST_ROAD_COMMAND_REUSE_VERIFY','NF_TEST_THREADED_EPOCH','NF_TEST_SHARED_SOURCE_EPOCH','NF_TEST_SHARED_SOURCE_RETIRE_EACH_CAPTURE','NF_TEST_SHARED_MOTION_CAPTURE','NF_TEST_THREAD_CPU_PROFILE','NF_TEST_MOTION_OWNER_PROFILE','NF_TEST_MOTION_CAPTURE_PROFILE','NF_TEST_SPLIT_STAGE_PROFILE','NF_TEST_SPLIT_PROFILE_SYNC','NF_TEST_PAGE_STAGE_PROFILE','NF_TEST_COMPLETE_CAPTURE_PROFILE']:
 if os.environ.get(flag)=='1':env[flag]='1'
if os.environ.get('NF_TEST_SPLIT_SCRATCH_REUSE')=='1':env['NF_TEST_SPLIT_SCRATCH_REUSE']='1'
readback=os.environ.get('NF_TEST_COMPLETE_READBACK')=='1'
if readback:env.pop('NF_THREADED_NO_READBACK',None);env['NF_TEST_COMPLETE_EXPORT']='1'
seconds=int(os.environ.get('NF_TEST_MOTION_SECONDS','4'));assert 4<=seconds<=20
r=subprocess.run([str(p/'threaded-preview.exe'),str(p/'visibility-probe-wide.dll'),session['rom'],session['state'],str(prefix),str(seconds)],env=env,capture_output=True,text=True,timeout=seconds+31);Path(str(prefix)+'-host.log').write_text(r.stdout+r.stderr);print(r.stdout[-2500:]);print(r.stderr);assert r.returncode==0,r.returncode
draws=list(csv.DictReader(Path(str(prefix)+'-worker.csv').open()));stable=[x for x in draws if x.get('frame_kind')=='5'];print('worker columns',list(draws[0]) if draws else [],'stable',len(stable));assert stable and all(int(x['result'])==0 for x in draws);assert all(x['frame_kind'] in ('4','5','6') for x in draws);assert any(x['frame_kind']=='4' for x in draws);assert any(x['frame_kind']=='6' for x in draws), 'No live motion published'
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint];assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
inputs=list(csv.DictReader(Path(str(prefix)+'-input.csv').open()))
try:
 for row in inputs:d.nf_frame(int(row['keys']))
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=Path(str(prefix)+'-baseline-'+name+'.bin');d.nf_dump(str(path).encode(),address,size);assert path.read_bytes()==Path(str(prefix)+'-'+name+'.bin').read_bytes()
finally:d.nf_close()
stats={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',r.stdout)}
rate=16777216/(280896*60)
for row in draws:
 slot=(float(row['target'])-int(row['source_base'])+8)/rate;assert abs(slot-round(slot))<1e-7
assert stats['complete_road_cache_hits']>0
if os.environ.get('NF_TEST_SHARED_MOTION_CAPTURE')=='1':assert stats['shared_source_cache_misses']>0
if os.environ.get('NF_TEST_SHARED_SOURCE_RETIRE_EACH_CAPTURE')=='1':assert stats['shared_source_cache_clears']>1
if os.environ.get('NF_TEST_SHARED_SOURCE_EPOCH')=='1':
 assert stats['epoch_cuts']==1 and stats['stale']>=1 and stats['shared_source_cache_clears']>=2
 assert re.search(r'shared_epoch_inflight kind=6 epoch=\d+ shared=1',r.stdout)
 cut=stats['cut_ns'];epoch=stats['cut_epoch']
 assert all(int(row['epoch'])>=epoch for row in draws if row['committed']=='1' and int(row['commit_begin_ns'])>=cut), 'Old epoch committed after cut'
 assert any(int(row['epoch'])==epoch and row['frame_kind']=='6' and row['committed']=='1' for row in draws), 'No new epoch motion resumed'
if readback:assert stats['complete_stable_verified']==6 and stats['complete_ordered_verified']==6 and stats['complete_motion_verified']==6
report=dict(complete_readback_requested=readback,host_stats=stats,original_presentation_clock_grid_verified=True,result='PASS',prefix=str(prefix),stable_worker_draws=len(stable),ordered_worker_draws=sum(x["frame_kind"]=="4" for x in draws),frame_kind_counts={k:sum(x["frame_kind"]==k for x in draws) for k in sorted(set(x["frame_kind"] for x in draws))},original_updates=len(inputs),original_ram_exact=True,scope='Actual queued worker sampled motion and complete snapshots at unchanged fractional presentation targets; no smooth60fps gameplay proof');(p/'threaded-motion-complete-test.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

