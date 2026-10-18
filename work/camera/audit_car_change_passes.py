"""Fresh original ledger audit of every pass across two car-change boundaries."""
from pathlib import Path
import json, ctypes as C, struct, hashlib, csv
p=Path(__file__).resolve().parent
# Reuse the existing read-only bridge declarations, without its replay/test body.
bootstrap=(p/'diagnose_late_model_pairs.py').read_text().split("assert d.nf_init(session['rom'].encode(),b'')")[0]
exec(compile(bootstrap,str(p/'diagnose_late_model_pairs.py'),'exec'))
prefix=p/'prototype-runs/threaded-prepared-4c0a478bbea14eedbc3a639513b0b9d6'
session=json.loads(Path(str(prefix)+'-session.json').read_text())
commands=d.nf_live_completed_draw_root_commands
commands.argtypes=[C.c_uint64,U,U,P,U,P]
root_pose=d.nf_live_completed_draw_root
root_pose.argtypes=[C.c_uint64,U,U,P,P]
timing=d.nf_live_completed_draw_timing
timing.argtypes=[C.c_uint64,U,U,P]
records=[];seen=set();updates=0
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 rom=Path(session['rom']).read_bytes()
 assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024)
 d.nf_live_surface_audit_enable(1)
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  d.nf_frame(int(row['keys']));updates+=1
  identity=(latest.get('epoch'),latest.get('serial'))
  if not identity[0] or identity in seen:continue
  seen.add(identity);epoch,serial=identity
  if serial not in [20,21,22,23,24,36,37,38,39,40]:continue
  proj=(U*6)();assert projection(epoch,serial,0,proj)
  passes=[]
  for ordinal in range(proj[5]):
   values=(U*6)();assert projection(epoch,serial,ordinal,values)
   draw_timing=(U*6)();assert timing(epoch,serial,ordinal,draw_timing)
   out=P();size=Z();assert asset(epoch,serial,ordinal,C.byref(out),C.byref(size))
   try:data=C.string_at(out,size.value)
   finally:d.nf_scene_packet_free(out)
   material=parts(data);buffer=C.create_string_buffer(144*3604);count=U()
   assert commands(epoch,serial,ordinal,buffer,144,C.byref(count))
   identities=[]
   for i in range(count.value):
    command=buffer.raw[i*3604:(i+1)*3604]
    kind,owner,native_pass,mask,obj,source=struct.unpack_from('<6I',command)
    identities.append(dict(kind=kind,owner=owner,pass_id=native_pass,object=obj,source=source))
   assert sum(c['kind']==5 for c in identities)==1
   view=(U*12)();scratch=C.create_string_buffer(65536)
   assert root_pose(epoch,serial,ordinal,view,scratch)
   passes.append(dict(ordinal=ordinal,projection=list(values),timing=list(draw_timing),geometry_uv_sha256=hashlib.sha256(material['geometry']).hexdigest(),indices_sha256=hashlib.sha256(material['indices']).hexdigest(),camera=list(struct.unpack_from('<7d',data,48)),object_pose=list(struct.unpack_from('<7d',data,104)),root_matrix=list(view),commands=identities))
  records.append(dict(serial=serial,passes=passes))
finally:d.nf_close()
assert len(records)==10 and updates==278
links=[]
for a,b in zip(records,records[1:]):
 if b['serial']!=a['serial']+1:continue
 matches=[]
 for left in a['passes']:
  for right in b['passes']:
   if left['geometry_uv_sha256']==right['geometry_uv_sha256'] and left['indices_sha256']==right['indices_sha256']:
    matches.append(dict(older_pass=left['ordinal'],newer_pass=right['ordinal'],camera_equal=left['camera']==right['camera'],object_equal=left['object_pose']==right['object_pose'],projection_equal=left['projection'][:5]==right['projection'][:5]))
 links.append(dict(older=a['serial'],newer=b['serial'],counts=[len(a['passes']),len(b['passes'])],material_matches=matches))
report=dict(result='AUDITED',original_updates=updates,records=records,links=links,scope='Original owned pass assets/poses/order only. Matching mesh and indices identifies material continuity, not visibility correspondence or permission to omit a pass. No sampled rendering change.')
(p/'car-change-pass-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(links,indent=2))
