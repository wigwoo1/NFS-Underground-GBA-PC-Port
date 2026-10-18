import ctypes as C,json,struct,hashlib,threading
from pathlib import Path
r=Path('work/camera');rec=json.loads((r/'prototype-runs/slow-hud-1791448905477795700/captures.json').read_text())['records'][0]
data={k:Path(v['path']).read_bytes() for k,v in rec['files'].items()};owners={k:C.create_string_buffer(v) for k,v in data.items()};raw=data['frame'];header=struct.unpack_from('<6I2Q',raw);gn,hn,bn=header[2:5];hud=40+gn;background=hud+hn;text=background+bn
P=C.c_void_p;d=C.CDLL(str((r/'owned-gpu-playable-input-cache-candidate.dll').resolve()));d.nf_owned_gpu_draw_scene_clips_sky.argtypes=[P,C.c_size_t,P,P,P,C.c_uint,P,P,C.c_size_t,C.c_double];d.nf_owned_gpu_read.argtypes=[P,C.c_size_t];d.nf_hud_input_cache_stats.argtypes=[P]
rgb=C.create_string_buffer(3840*2160*3);checks=[]
def stats():
 out=(C.c_uint64*3)();assert d.nf_hud_input_cache_stats(out)==1 and out[2]==0;return list(out)
def draw():return d.nf_owned_gpu_draw_scene_clips_sky(owners['frame'],len(raw),owners['camera'],owners['models'],owners['bounds'],rec['geometry_records'],owners['lower'],owners['upper'],15136,rec['sky_weight'])
def restore():C.memmove(owners['frame'],raw,len(raw))
def pixels():assert d.nf_owned_gpu_read(rgb,len(rgb))==0;return hashlib.sha256(rgb.raw).hexdigest()
try:
 assert d.nf_owned_gpu_window(0)==0 and draw()==0;baseline=pixels();assert draw()==0 and pixels()==baseline;initial=stats();assert initial[0]>0
 for label,offset,value,expected in [('wrong_row',hud,header[1]+1,24),('background_coverage',background+38400,2,25),('text_coverage',text+38400,2,25)]:
  restore();C.memmove(C.addressof(owners['frame'])+offset,struct.pack('<I',value) if label=='wrong_row' else bytes([value]),4 if label=='wrong_row' else 1)
  assert draw()==expected,(label,expected);stats();restore();assert draw()==0 and pixels()==baseline;checks.append(label)
 # Same pointer, changed HUD bytes, then sky-coverage rejection after the owned HUD copy.
 restore();owners['frame'][hud+100]=bytes([raw[hud+100]^1]);owners['frame'][background+38400+10560]=b'\x00';before=stats();rc=draw();assert rc==41,rc;failed=stats();assert failed[1]>before[1]
 restore();assert draw()==0 and pixels()==baseline;recovered=stats();assert recovered[1]>failed[1],'Recovery reused stale owned storage';checks.append('postcopy_sky_coverage_failure_recovery')
 # New epoch must miss even when HUD bytes are identical.
 restore();C.memmove(C.addressof(owners['frame'])+24,struct.pack('<Q',header[6]+1),8);before=stats();assert draw()==0 and pixels()==baseline;assert stats()[1]>before[1];checks.append('epoch_change')
 restore();assert draw()==0 and pixels()==baseline
 foreign=[];t=threading.Thread(target=lambda:foreign.append(draw()));t.start();t.join();assert foreign==[31];checks.append('foreign_thread')
 stats()
finally:assert d.nf_owned_gpu_close()==1
out=dict(result='PASS',checks=checks,baseline_sha256=baseline,scope='Malformed fullsubmission, same-pointer mutation, postcopy-error owned-cache certificate recovery, epoch and owner guards; legacy/fileload paths and live cadence pending.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/playable-input-cache-guards-20261008');cp.mkdir(exist_ok=True);(cp/'guards.json').write_text(json.dumps(out,indent=2));print(out)


