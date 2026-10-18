"""Offline original-eligibility command plan into native owned scene assembly."""
from pathlib import Path
import ctypes as C,json,struct,os
owned_bounds=bool(os.environ.get("NF_OWNED_BOUNDS"))
p=Path('work/camera');f=p/'overflow-scene-171';packet=(f/'old.bin').read_bytes();manifest=json.loads((f/'manifest.json').read_text());sections={t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+i*12) for i in range(5))}
assets={};wp=lp=8
for i in range(struct.unpack_from('<I',sections[2],4)[0]):
 n,w,h=struct.unpack_from('<3I',sections[2],wp);size=12+n*40+w*h*4;lit=struct.unpack_from('<I',sections[4],lp)[0];ls=20+w*h*64 if lit else 4;identity=struct.unpack_from('<5I',sections[5],8+i*20)
 key=identity[:1]+identity[2:3];value=(identity,sections[2][wp:wp+size],sections[4][lp:lp+ls])
 if key in assets:assert assets[key]==value
 assets[key]=value;wp+=size;lp+=ls
for source,a in (manifest['assets']|manifest.get('adjacent_assets',{})).items():
 assets.setdefault((2,int(source)),(a['identity'],(f/f'wall-{source}.bin').read_bytes(),struct.pack('<I',0)))
for source,a in manifest['road_assets'].items():
 assets.setdefault((1,int(source)),([1,manifest['state'],int(source),8,0],(f/f'road-{source}.bin').read_bytes(),struct.pack('<I',0)))
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));d.nf_assembly_create.restype=C.c_void_p
for name in ('nf_assembly_destroy','nf_scene_packet_free'):getattr(d,name).argtypes=[C.c_void_p]
d.nf_assembly_bounds.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p]
d.nf_assembly_surface.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];d.nf_assembly_model.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t];d.nf_assembly_finish.argtypes=[C.c_void_p]+[C.c_uint32]*4+[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p]
model_identity=struct.unpack_from('<5I',sections[5],len(sections[5])-20);header=struct.unpack_from('<8I',packet);cases=[]
coverage=[]
for fraction in ('0.25','0.5','0.75'):
 trace=json.loads((p/f'sampled-object-dispatch-{fraction}-motion-tests.json').read_text());missing=[]
 for draw in trace['draws']:
  kind={'road':1,'wall':2,'model':3}[draw['kind']]
  if kind!=3 and (kind,draw['source']) not in assets:missing.append([kind,draw['source']])
 coverage.append(dict(alpha=float(fraction),missing=missing))
for alpha in ('0.25','0.5','0.75'):
 if next(c for c in coverage if c['alpha']==float(alpha))['missing']:continue
 trace=json.loads((p/f'sampled-object-dispatch-{alpha}-motion-tests.json').read_text());control=json.loads((p/f'sampled-object-dispatch-{alpha}-tests.json').read_text());assert trace['draws']==control['draws']
 commands=json.loads((p/f'sampled-command-plan-{alpha}.json').read_text())['commands'];assert len(commands)==len(trace['draws'])
 owner=d.nf_assembly_create();assert owner;bounds=[];ids=[]
 native_roads={(r['source'],r['owner']):r['native_clip_bounds'] for r in json.loads((p/f'road-clip-inputs-{alpha}-motion-writes-full.json').read_text())['cases']} if owned_bounds else {}
 try:
  for command,draw in zip(commands,trace['draws']):
   kind,source,obj,invocation=command[:4];assert source==draw['source'] and invocation==draw['owner'];call=trace['calls'][invocation]
   if kind==3:
    model=(p/f'sampled-model-{alpha}-motion.bin').read_bytes();assert d.nf_assembly_model(owner,struct.pack('<5I',*model_identity),model,len(model));continue
   identity,surface,lighting=assets[kind,source]
   if obj:surface=(p/f'sampled-object-surface-{alpha}-motion.bin').read_bytes()
   assert d.nf_assembly_surface(owner,struct.pack('<5I',*identity),surface,len(surface),lighting,len(lighting));ids.append(identity);bounds.append(call['record'][1:5])
   if owned_bounds:
    selected=native_roads[source,invocation] if kind==1 else call['record'][1:5]
    assert d.nf_assembly_bounds(owner,len(ids)-1,float(alpha),struct.pack('<4H',*selected))
  out=C.c_void_p();size=C.c_size_t();assert d.nf_assembly_finish(owner,*header[4:8],sections[4][-131072:],131072,C.byref(out),C.byref(size))
  try:raw=C.string_at(out,size.value)
  finally:d.nf_scene_packet_free(out)
  (f/f'{"assembly-owned" if owned_bounds else "composed"}-{alpha}.bin').write_bytes(raw)
  # Packet groups roads then walls; each occurrence keeps separate bounds.
  ordered=[i for kind in (1,2) for i,identity in enumerate(ids) if identity[0]==kind]
  clips=struct.pack('<5Id',0x3150434e,*header[4:7],len(ids),float(alpha))
  for i in ordered:clips+=struct.pack('<5I4H',*ids[i],*bounds[i])
  (f/f'composed-{alpha}.clips').write_bytes(clips)
  cases.append(dict(alpha=float(alpha),commands=len(commands),surfaces=len(ids),bytes=len(raw)))
 finally:d.nf_assembly_destroy(owner)
report=dict(result='INCOMPLETE' if any(c['missing'] for c in coverage) else 'PASS',coverage=coverage,cases=cases,scope='Native owned assembly of complete sampled offline draw trace, with regenerated car/object surface and retained scene assets/lighting. Original eligibility and endpoint memberships retained; no live rendering/timing proof. Owned per-surface packet bounds enabled when NF_OWNED_BOUNDS is set; coverage fidelity and live integration remain incomplete.')
(p/('assembly-owned-compose-tests.json' if owned_bounds else 'sampled-scene-compose-tests.json')).write_text(json.dumps(report,indent=2));print(report)
