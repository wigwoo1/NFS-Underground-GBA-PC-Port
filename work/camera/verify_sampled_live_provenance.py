"""Fresh original-input replay byte provenance for mixed sampled/held dense capture."""
import ctypes as C,csv,json,hashlib,re,struct,sys
from pathlib import Path
p=Path(__file__).resolve().parent;m=Path(sys.argv[1]);session=json.loads(m.read_text(encoding='utf-8-sig'));prefix=Path(session['prefix']);assert session['sampled_draw_scene'] and session['status']=='HOST_COMPLETE'
for name in ['rom','state']:assert hashlib.sha256(Path(session[name]).read_bytes()).hexdigest()==session[name+'_sha256'].lower()
log=Path(str(prefix)+'-host.log').read_text();decisions={float(t):int(ok) for t,ok in re.findall(r'selection_sampled_root target=([\d.]+).*?accepted=(\d+)',log)}
files=sorted(prefix.parent.glob(prefix.name+'-dense-*-native-source.json'));assert len(files)==session['dense_frames'];requests=[]
for file in files:
 meta=json.loads(file.read_text());camera=Path(str(file).replace('-native-source.json','-owned-cameras.bin')).read_bytes();magic,version,endpoints,count=struct.unpack_from('<4I',camera);assert (magic,version,endpoints)==(0x5043464e,1,0);alpha=struct.unpack_from('<d',camera,16)[0];assert len(camera)==24+count*56
 match=[ok for t,ok in decisions.items() if abs(t-meta['target'])<1e-9];assert len(match)==1
 requests.append(dict(meta=meta,file=file,alpha=alpha,cameras=camera[24:],count=count,sampled=bool(match[0])))
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p];assert crt._putenv_s(b'NF_CAPTURE_MODEL_VIEWS',b'1')==0
assert crt._putenv_s(b'NF_CAPTURE_WALL_OUTPUT_INDICES',b'1' if session.get('display_palette') else b'')==0
assert crt._putenv_s(b'NF_TEST_INDEXED_ENTRANTS',b'1' if session.get('indexed_entrants') else b'')==0
assert crt._putenv_s(b'NF_TEST_FOCAL_SAMPLE',b'1' if session.get('focal_sample') else b'')==0
P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t;d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_live_visibility_enable.argtypes=[P,Z,Z];d.nf_scene_packet_free.argtypes=[P]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z);latest={}
@Sink
def sink(ctx,e,data,size):latest.update(epoch=e,serial=struct.unpack_from('<I',C.string_at(data,20),16)[0]);return 1
sample_scene=getattr(d,'nf_live_completed_draw_scene_packet_transition' if session.get('transition_draw_scene') else 'nf_live_completed_draw_scene_packet_sample')
d.nf_native_scene_sink.argtypes=[Sink,P];sample_scene.argtypes=[C.c_uint64,U,U,C.c_double,P,P,P,U,P];d.nf_live_completed_draw_scene_packet.argtypes=[C.c_uint64,U,P,P,P,U,P]
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0);checks=[]
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1);rom=Path(session['rom']).read_bytes();assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024);d.nf_live_surface_audit_enable(1)
 rows=list(csv.DictReader(Path(str(prefix)+'-input.csv').open()));wanted=max(x['meta']['newer_handle'] for x in requests)
 updates=0
 for row in rows:
  assert int(row['index'])==updates;d.nf_frame(int(row['keys']));updates+=1
  if latest.get('serial',-1)>=wanted:break
 assert latest['serial']>=wanted
 for item in requests:
  meta=item['meta'];assert latest['epoch']==meta['epoch'];out=P();size=Z();poses=C.create_string_buffer(8064);count=U()
  if item['sampled']:ok=sample_scene(meta['epoch'],meta['older_handle'],meta['newer_handle'],item['alpha'],C.byref(out),C.byref(size),poses,144,C.byref(count))
  else:ok=d.nf_live_completed_draw_scene_packet(meta['epoch'],meta['older_handle'],C.byref(out),C.byref(size),poses,144,C.byref(count))
  assert ok
  try:raw=C.string_at(out,size.value)
  finally:d.nf_scene_packet_free(out)
  captured=Path(str(item['file']).replace('-native-source.json','-native-scene.bin')).read_bytes();assert raw==captured,'Packet byte provenance mismatch';assert count.value==item['count'] and poses.raw[:count.value*56]==item['cameras'],'Command camera byte provenance mismatch'
  checks.append(dict(target=meta['target'],sampled=item['sampled'],packet_sha256=hashlib.sha256(raw).hexdigest(),command_cameras_exact=True,alpha_binary_exact=item['alpha']))
finally:d.nf_close()
report=dict(result='PASS',original_updates=updates,checks=checks,scope='Fresh recorded original-input replay reproduces complete dense scene and per-command camera bytes, sampled versus held classified separately. Shared native extractor; independent GPU geometry/motion and fullscene60fps remain unverified.');Path(str(prefix)+'-sampled-provenance.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(result='PASS',frames=len(checks),sampled=sum(x['sampled'] for x in checks),held=sum(not x['sampled'] for x in checks),original_updates=updates)))
