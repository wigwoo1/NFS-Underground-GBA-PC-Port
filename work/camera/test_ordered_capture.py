"""Actual original-update producer capture, no saved fixture as input."""
from pathlib import Path
import ctypes as C,csv,json,hashlib
p=Path(__file__).resolve().parent
exec(compile((p/'test_live_owned_indexed_copy.py').read_text().split("\nassert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'test_live_owned_indexed_copy.py'),'exec'))
helper=C.CDLL(str(p/'ordered-capture-test.dll'));capture=helper.nf_ordered_capture_test;capture.argtypes=[P,C.c_uint64,U,U,U,U,P];helper.nf_ordered_capture_test_free.argtypes=[P]
class Owned(C.Structure):
 _fields_=[(x,P) for x in ['older','newer','hud','text']]+[(x,Z) for x in ['older_size','newer_size','hud_size','text_size']]+[('epoch',C.c_uint64),('refresh',U),('cut',U)]
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
assert crt._putenv_s(b"NF_TEST_COMPLETE_ROAD_CACHE",b"1")==0
helper.nf_complete_road_cache_stats_test.argtypes=[P]
clones=[];seen=set();report=[]
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024);d.nf_live_surface_audit_enable(1);assert d.nf_bitmap_text_enable(1) and d.nf_layer_queue_enable(1)
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  d.nf_frame(int(row['keys']));e,s=latest.get('epoch'),latest.get('serial')
  if s in seen or s not in [22,38]:continue
  seen.add(s);refresh=d.nf_layer_queue_latest();cut=6 if s==22 else 99;owner=P(123)
  assert not capture(d._handle,e,s-1,s,refresh,cut+1,C.byref(owner)) and owner.value==123
  assert capture(d._handle,e,s-1,s,refresh,cut,C.byref(owner));v=C.cast(owner,C.POINTER(Owned)).contents;parts={}
  for kind in ['older','newer','hud','text']:
   raw=C.string_at(getattr(v,kind),getattr(v,kind+'_size'));name=f'split-owner-{s-1 if kind=="older" else s}.bin' if kind in ['older','newer'] else f'road-bundle-{s}-owned-{kind}.bin'
   assert raw==(p/name).read_bytes(),(s,kind);parts[kind]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
  clones.append((owner,parts));report.append(dict(serial=s,epoch=v.epoch,refresh=v.refresh,cut=v.cut,parts=parts))
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/('ordered-capture-check-'+name+'.bin');d.nf_dump(str(path).encode(),address,size);raw=path.read_bytes();path.unlink();assert raw==Path(str(prefix)+'-'+name+'.bin').read_bytes()
finally:d.nf_close()
assert len(clones)==2
stats=(C.c_uint64*2)();helper.nf_complete_road_cache_stats_test(stats);assert stats[0]>=4 and stats[1]==4;helper.nf_complete_road_cache_clear_test()
for owner,parts in clones:
 v=C.cast(owner,C.POINTER(Owned)).contents
 for kind,meta in parts.items():assert hashlib.sha256(C.string_at(getattr(v,kind),meta['bytes'])).hexdigest()==meta['sha256']
 helper.nf_ordered_capture_test_free(owner)
result=dict(cache_hits=stats[0],cache_misses=stats[1],result='PASS',captures=report,full_original_ram_exact=True,owned_after_bridge_close=True,owned_after_cache_clear=True,wrong_cut_atomic=True,scope='Producer capture only; not scheduled live rendering or 60fps gameplay')
(p/'ordered-capture-test.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
