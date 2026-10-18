from pathlib import Path
p=Path('work/camera');s=(p/'capture_owned_clip_writers.py').read_text()
s=s.replace('try:\n for row in rows:assert d.nf_frame(int(row[\'keys\']))',"d.nf_owned_graph_live_read.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]\nlive_enabled=False\ntry:\n for row in rows:\n  if not live_enabled and d.nf_native_scene_refresh()>=8754:assert d.nf_owned_graph_live_enable(1);live_enabled=True\n  assert d.nf_frame(int(row['keys']))\n n=C.c_size_t();assert d.nf_owned_graph_live_read(None,0,C.byref(n));owned=C.create_string_buffer(n.value);assert d.nf_owned_graph_live_read(owned,n.value,C.byref(n));(p/'owned-live-graph-snapshot.bin').write_bytes(owned.raw)\n d.nf_owned_graph_live_material_read.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];assert d.nf_owned_graph_live_material_read(None,0,C.byref(n));materials=C.create_string_buffer(n.value);assert d.nf_owned_graph_live_material_read(materials,n.value,C.byref(n));(p/'owned-live-graph-materials.bin').write_bytes(materials.raw)\n d.nf_owned_graph_live_objects_read.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];assert d.nf_owned_graph_live_objects_read(None,0,C.byref(n));objects=C.create_string_buffer(n.value);assert d.nf_owned_graph_live_objects_read(objects,n.value,C.byref(n));(p/'owned-live-graph-objects.bin').write_bytes(objects.raw)\n d.nf_owned_graph_live_callbacks_read.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];assert d.nf_owned_graph_live_callbacks_read(None,0,C.byref(n));callbacks=C.create_string_buffer(max(1,n.value));assert d.nf_owned_graph_live_callbacks_read(callbacks,n.value,C.byref(n));(p/'owned-live-graph-callbacks.bin').write_bytes(callbacks.raw[:n.value])")
s=s.replace('finally:d.nf_owned_object_palette_trace','finally:d.nf_owned_graph_live_enable(0);d.nf_owned_object_palette_trace')
s=s.replace("  assert d.nf_frame(int(row['keys']))", "  assert d.nf_frame(int(row['keys']))\n  if live_enabled:\n   d.nf_owned_graph_live_callbacks_read.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];cbn=C.c_size_t();assert d.nf_owned_graph_live_callbacks_read(None,0,C.byref(cbn))\n   if cbn.value:\n    cb=C.create_string_buffer(cbn.value);assert d.nf_owned_graph_live_callbacks_read(cb,cbn.value,C.byref(cbn));(p/'owned-live-callbacks-nonempty.bin').write_bytes(cb.raw)\n    d.nf_owned_graph_live_associations_read.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];an=C.c_size_t();assert d.nf_owned_graph_live_associations_read(None,0,C.byref(an));association=C.create_string_buffer(max(1,an.value));assert d.nf_owned_graph_live_associations_read(association,an.value,C.byref(an));(p/'owned-live-associations-nonempty.bin').write_bytes(association.raw[:an.value])")
exec(compile(s,'live_graph_capture','exec'))
raw=(p/'owned-graph-snapshots.bin').read_bytes();offset=0;latest=None
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);n=32+(896+h[4]+h[5] if h[6] else 0);latest=raw[offset:offset+n];offset+=n
assert offset==len(raw) and latest==(p/'owned-live-graph-snapshot.bin').read_bytes()
print('PASS_FILELESS_GRAPH_SNAPSHOT_PARITY',len(latest))

refresh=struct.unpack_from('<I',latest,4)[0];raw=(p/'owned-graph-materials.bin').read_bytes();offset=0;selected=[]
while offset<len(raw):
 h=struct.unpack_from('<12I',raw,offset);n=120+(h[8] if h[9]==1 else 0)
 if h[1]==refresh:selected.append(raw[offset:offset+n])
 offset+=n
assert offset==len(raw) and b''.join(selected)==(p/'owned-live-graph-materials.bin').read_bytes()
print('PASS_FILELESS_GRAPH_MATERIAL_PARITY',len(selected),sum(map(len,selected)))

from owned_graph_packet import GraphPacket
h=struct.unpack_from('<8I',latest);start=928;geometry=latest[start:start+h[4]];start+=h[4]
packet=GraphPacket(h[1],h[2],latest[32:928],geometry,latest[start:start+h[5]],(p/'owned-live-graph-materials.bin').read_bytes())
encoded=packet.encode();assert GraphPacket.decode(encoded)==packet
(p/'owned-live-graph-packet.ngp').write_bytes(encoded)
print('PASS_FILELESS_GRAPH_PACKET',len(packet.validate()),len(encoded))

raw=(p/'owned-graph-objects.bin').read_bytes();offset=0;selected=[]
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);n=128+h[6]
 if h[1]==refresh:selected.append(raw[offset:offset+n])
 offset+=n
assert len(selected)==221 and b''.join(selected)==(p/'owned-live-graph-objects.bin').read_bytes()
print('PASS_FILELESS_GRAPH_OBJECT_PARITY',len(selected),sum(map(len,selected)))

raw=(p/'owned-object-eligibility.bin').read_bytes();camera=latest[288:336]
selected=[raw[o:o+244] for o in range(0,len(raw),244) if raw[o+196:o+244]==camera]
assert b''.join(selected)==(p/'owned-live-graph-callbacks.bin').read_bytes()
print('PASS_FILELESS_CALLBACK_CAPTURE_PARITY',len(selected))

nonempty=(p/'owned-live-callbacks-nonempty.bin').read_bytes();assert nonempty and len(nonempty)%244==0
camera=nonempty[196:244];raw=(p/'owned-object-eligibility.bin').read_bytes();selected=b''.join(raw[o:o+244] for o in range(0,len(raw),244) if raw[o+196:o+244]==camera)
assert selected==nonempty
print('PASS_FILELESS_NONEMPTY_CALLBACK_PARITY',len(nonempty)//244)

association=(p/'owned-live-associations-nonempty.bin').read_bytes();assert association and len(association)%400==0
raw=(p/'owned-object-associations.bin').read_bytes();expected=b''.join(raw[o:o+400] for o in range(0,len(raw),400) if raw[o+352:o+400]==camera)
assert association==expected
ids={struct.unpack_from('<I',association,o+28)[0] for o in range(0,len(association),400)}
assert all(struct.unpack_from('<I',nonempty,o+28)[0] in ids for o in range(0,len(nonempty),244))
print('PASS_FILELESS_LIVE_ASSOCIATION_CALLBACK_JOIN',len(ids),len(nonempty)//244)
