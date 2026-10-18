"""Compare complete live scanline snapshots across checkpoint reload and Start inputs."""
from pathlib import Path
import ctypes as C,os,sys,subprocess,json,hashlib,uuid
p=Path(__file__).resolve().parent
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
if '--worker' in sys.argv:
 mode=sys.argv[-1];d=C.CDLL(str(p.parent/'nfsprobe.dll' if mode=='baseline' else p/'visibility-probe-wide.dll'))
 d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
 assert d.nf_init(rom,b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
 rows=[];modes=[];reloads=0
 if mode!='baseline':
  d.nf_native_scene_epoch.restype=C.c_uint64
  d.nf_layer_queue_row.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
  assert d.nf_layer_queue_enable(1)
  size=d.nf_layer_row_size();buf=C.create_string_buffer(size)
 try:
  for frame in range(120):
   if frame==80:
    if mode!='baseline':old_epoch=d.nf_native_scene_epoch();old_refresh=d.nf_layer_queue_latest()
    assert d.nf_state(str(p.parent/'driving.state').encode(),0);reloads+=1
    if mode!='baseline':
     sentinel=C.create_string_buffer(b'Q'*size,size)
     assert not d.nf_layer_queue_row(old_epoch,old_refresh,0,sentinel,size) and sentinel.raw==b'Q'*size
   keys=8 if frame in (24,48,96) else 1
   d.nf_frame(keys);modes.append(d.nf_read(0x03005f14,4))
   if mode!='baseline':
    digest=hashlib.sha256();epoch=d.nf_native_scene_epoch();refresh=d.nf_layer_queue_latest()
    for y in range(160):
     assert d.nf_layer_queue_row(epoch,refresh,y,buf,size)
     digest.update(buf.raw)
    rows.append(digest.hexdigest())
  hashes={};prefix=p/'prototype-runs'/('dirty-reload-'+uuid.uuid4().hex)
  for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
   target=Path(str(prefix)+'-'+name+'.bin');d.nf_dump(str(target).encode(),base,size);hashes[name]=hashlib.sha256(target.read_bytes()).hexdigest()
  stats=None
  if mode=='dirty':
   values=(C.c_uint64*3)();d.nf_layer_snapshot_dirty_stats(values);stats=list(values)
   assert stats[0]>0 and stats[0]==stats[1] and stats[2]==0
 finally:d.nf_close()
 print(json.dumps(dict(mode=mode,rows=rows,modes=modes,ram=hashes,reloads=reloads,dirty_stats=stats)))
else:
 output=p/'layer-dirty-reload-tests.json';output.write_text(json.dumps(dict(result='RUNNING')))
 try:
  results=[]
  for mode in ('normal','dirty','baseline'):
   env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
   if mode=='dirty':env.update(NF_LAYER_DIRTY='1',NF_VERIFY_LAYER_DIRTY='1')
   result=subprocess.run([sys.executable,__file__,'--worker',mode],env=env,capture_output=True,text=True,check=True,timeout=60)
   results.append(json.loads(result.stdout))
  normal,dirty,baseline=results
  assert normal['rows']==dirty['rows'] and len(normal['rows'])==120
  assert normal['ram']==dirty['ram']==baseline['ram'] and normal['modes']==dirty['modes']==baseline['modes']
  report=dict(result='PASS',full_scanline_rows_compared=120*160,checkpoint_reload_count=1,old_snapshot_rejected=True,mode_values=sorted(set(normal['modes'])),dirty_stats=dirty['dirty_stats'],ram_hashes=normal['ram'],scope='All complete hardware rows compared byte-hash exactly between default and audited dirty capture; identical final original bridge RAM across one read-only checkpoint reload and scripted Start inputs. Mode values report observed game modes only; no inference of menu transitions or physical input/smooth60fps.')
  output.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 except Exception as error:output.write_text(json.dumps(dict(result='FAIL',error=str(error)),indent=2));raise
