from pathlib import Path
import ctypes as C,struct,json
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0]
exec(compile(setup,'capture_setup','exec'))
d.nf_owned_input_list_trace.argtypes=[C.c_char_p]
d.nf_owned_eligibility_trace.argtypes=[C.c_char_p]
d.nf_owned_filter_trace.argtypes=[C.c_char_p]
d.nf_owned_association_trace.argtypes=[C.c_char_p]
d.nf_owned_chain_trace.argtypes=[C.c_char_p]
d.nf_owned_supplement_textures_trace.argtypes=[C.c_char_p]
d.nf_owned_supplement_geometry_trace.argtypes=[C.c_char_p]
d.nf_owned_supplement_trace.argtypes=[C.c_char_p]
d.nf_owned_region_entry_trace.argtypes=[C.c_char_p]
d.nf_owned_descriptor_trace.argtypes=[C.c_char_p]
d.nf_owned_material_resolution_trace.argtypes=[C.c_char_p]
d.nf_owned_wall_owner_trace.argtypes=[C.c_char_p]
d.nf_owned_object_palette_trace.argtypes=[C.c_char_p]
d.nf_owned_object_pose_trace.argtypes=[C.c_char_p]
d.nf_owned_object_texture_trace.argtypes=[C.c_char_p]
d.nf_owned_graph_models_trace.argtypes=[C.c_char_p]
d.nf_owned_graph_objects_trace.argtypes=[C.c_char_p]
d.nf_owned_graph_snapshot_trace.argtypes=[C.c_char_p]
d.nf_owned_graph_material_trace.argtypes=[C.c_char_p]
d.nf_owned_graph_trace.argtypes=[C.c_char_p]
d.nf_owned_traversal_trace.argtypes=[C.c_char_p]
d.nf_owned_projected_trace.argtypes=[C.c_char_p]
d.nf_owned_portal_trace.argtypes=[C.c_char_p]
d.nf_owned_partition_trace.argtypes=[C.c_char_p]
d.nf_owned_clip_trace.argtypes=[C.c_char_p]
d.nf_owned_clip_store_trace.argtypes=[C.c_char_p]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
assert d.nf_owned_input_list_trace(str(p/'owned-object-input-lists.bin').encode())
assert d.nf_owned_eligibility_trace(str(p/'owned-object-eligibility.bin').encode())
assert d.nf_owned_filter_trace(str(p/'owned-object-filter.bin').encode())
assert d.nf_owned_association_trace(str(p/'owned-object-associations.bin').encode())
assert d.nf_owned_chain_trace(str(p/'owned-object-chains.bin').encode())
assert d.nf_owned_supplement_textures_trace(str(p/'owned-supplement-textures.bin').encode())
assert d.nf_owned_supplement_geometry_trace(str(p/'owned-supplement-geometry.bin').encode())
assert d.nf_owned_supplement_trace(str(p/'owned-supplements.bin').encode())
assert d.nf_owned_region_entry_trace(str(p/'owned-region-entries.bin').encode())
assert d.nf_owned_descriptor_trace(str(p/'owned-descriptor-selection.bin').encode())
assert d.nf_owned_material_resolution_trace(str(p/'owned-material-resolution.bin').encode())
assert d.nf_owned_wall_owner_trace(str(p/'owned-wall-owners.bin').encode())
assert d.nf_owned_object_palette_trace(str(p/'owned-object-palettes.bin').encode())
assert d.nf_owned_object_pose_trace(str(p/'owned-object-poses.bin').encode())
assert d.nf_owned_object_texture_trace(str(p/'owned-object-textures.bin').encode())
assert d.nf_owned_graph_models_trace(str(p/'owned-graph-models.bin').encode())
assert d.nf_owned_graph_objects_trace(str(p/'owned-graph-objects.bin').encode())
assert d.nf_owned_graph_snapshot_trace(str(p/'owned-graph-snapshots.bin').encode())
assert d.nf_owned_graph_material_trace(str(p/'owned-graph-materials.bin').encode())
assert d.nf_owned_graph_trace(str(p/'owned-portal-graphs.bin').encode())
assert d.nf_owned_traversal_trace(str(p/'owned-traversals.bin').encode())
assert d.nf_owned_projected_trace(str(p/'owned-projected-portals.bin').encode())
assert d.nf_owned_portal_trace(str(p/'owned-portals.bin').encode())
assert d.nf_owned_partition_trace(str(p/'owned-partitions.bin').encode())
target=p/'owned-clip-writers-runtime.bin';assert d.nf_owned_clip_trace(str(target).encode());assert d.nf_world_trace(b'');assert d.nf_owned_clip_store_trace(str(p/'owned-clip-stores.bin').encode())
try:
 for row in rows:assert d.nf_frame(int(row['keys']))
 for name,address,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  f=p/f'clip-trace-{name}.bin';d.nf_dump(str(f).encode(),address,n);assert f.read_bytes()==Path(str(source)+'-'+name+'.bin').read_bytes()
finally:d.nf_owned_object_palette_trace(None);d.nf_owned_object_pose_trace(None);d.nf_owned_object_texture_trace(None);d.nf_owned_graph_models_trace(None);d.nf_owned_graph_objects_trace(None);d.nf_owned_graph_snapshot_trace(None);d.nf_owned_graph_material_trace(None);d.nf_owned_supplement_textures_trace(None);d.nf_owned_material_resolution_trace(None);d.nf_owned_supplement_geometry_trace(None);d.nf_owned_input_list_trace(None);d.nf_owned_eligibility_trace(None);d.nf_owned_filter_trace(None);d.nf_owned_association_trace(None);d.nf_owned_chain_trace(None);d.nf_owned_supplement_trace(None);d.nf_owned_region_entry_trace(None);d.nf_owned_descriptor_trace(None);d.nf_owned_wall_owner_trace(None);d.nf_owned_graph_trace(None);d.nf_owned_traversal_trace(None);d.nf_owned_projected_trace(None);d.nf_owned_portal_trace(None);d.nf_owned_partition_trace(None);d.nf_owned_clip_store_trace(None);d.nf_owned_clip_trace(None);d.nf_world_trace(None);d.nf_close()
raw=target.read_bytes();assert len(raw)%104==0
records=[]
for offset in range(0,len(raw),104):
 v=struct.unpack_from('<26I',raw,offset);assert v[0]==0x314c434e
 records.append(dict(pc=hex(v[1]),refresh=v[2],state=hex(v[3]),source=hex(v[4]),source_halfwords=list(struct.unpack_from('<8H',raw,offset+88))))
assert records
r=dict(result='PASS_CLIP_WRITER_RUNTIME_CAPTURE',records=records,original_ram_exact=True,scope='Read-only executed provenance, bounded4096records; upstream clipping-record construction still unresolved.')
(p/'owned-clip-writers-runtime.json').write_text(json.dumps(r,indent=2));print(r['result'],len(records),sorted(set(x['pc'] for x in records)))

raw=(p/'owned-clip-stores.bin').read_bytes();assert len(raw)%84==0
stores=[]
for offset in range(0,len(raw),84):
 v=struct.unpack_from('<21I',raw,offset);assert v[0]==0x3153434e
 stores.append(dict(pc=hex(v[1]),refresh=v[2],address=hex(v[3]),bytes=v[4],registers=list(v[5:])))
assert stores
(p/'owned-clip-stores.json').write_text(json.dumps(dict(result='PASS_CLIP_RECORD_STORE_PROVENANCE',stores=stores,original_ram_exact=True),indent=2));print('CLIP_RECORD_STORES',len(stores),sorted(set(x['pc'] for x in stores)))
