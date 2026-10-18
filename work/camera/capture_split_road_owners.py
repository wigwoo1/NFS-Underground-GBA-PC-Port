"""Capture immutable adjacent page owners for original HUD split frames."""
from pathlib import Path
import ctypes as C,csv,json,struct,hashlib
p=Path(__file__).resolve().parent
exec(compile((p/'test_live_owned_indexed_copy.py').read_text().split("\nassert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'test_live_owned_indexed_copy.py'),'exec'))
owners={};clones=[];seen=set()
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024);d.nf_live_surface_audit_enable(1)
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  d.nf_frame(int(row['keys']));e,s=latest.get('epoch'),latest.get('serial')
  if not e or s in seen:continue
  seen.add(s)
  if s not in [21,22,37,38]:continue
  pointer=P();size=Z();ok=road_bundle_get(e,s,C.byref(pointer),C.byref(size))
  if not ok:owners[s]=dict(available=False,epoch=e);continue
  raw=C.string_at(pointer,size.value);assert road_bundle_validate(raw,len(raw));h=struct.unpack_from('<8I',raw);inner=struct.unpack_from('<16I',raw,h[5]);path=p/f'split-owner-{s}.bin';path.write_bytes(raw)
  owners[s]=dict(available=True,epoch=e,serial=s,page=inner[5],begin=inner[3],end=inner[4],road_assets=h[3],sha256=hashlib.sha256(raw).hexdigest(),path=path.name);clones.append((pointer,raw))
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/('split-owner-check-'+name+'.bin');d.nf_dump(str(path).encode(),address,size);raw=path.read_bytes();path.unlink();assert raw==Path(str(prefix)+'-'+name+'.bin').read_bytes()
finally:d.nf_close()
for pointer,raw in clones:assert C.string_at(pointer,len(raw))==raw;d.nf_live_ordered_bundle_free(pointer)
plans=[]
for check in json.loads((p/'road-bundle-hud-audit.json').read_text())['checks']:
 serial=check['serial'];pair=[owners[serial-1],owners[serial]];segments=[]
 for run in check['runs']:
  matches=[x for x in pair if x['available'] and x['page']==run['state']['page'] and x['epoch']==check['epoch'] and x['end']<=check['refresh']]
  segments.append(dict(begin=run['begin'],end=run['end'],page=run['state']['page'],owner_serial=matches[0]['serial'] if len(matches)==1 else None))
 plans.append(dict(refresh=check['refresh'],segments=segments,complete=all(x['owner_serial'] is not None for x in segments)))
report=dict(result='AUDITED',owners=owners,plans=plans,full_original_ram_exact=True,lifetime_after_close=True,scope='Adjacentoriginalpageowner availability and temporal metadata only; GPU split/HUDcomposition notyetverified')
(p/'split-road-owners.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
