import ctypes as C,json
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'layer-snapshot-profile-candidate.dll').resolve()));d.nf_layer_snapshot_create.restype=C.c_void_p;d.nf_layer_snapshot_add.argtypes=[C.c_void_p,C.c_void_p];d.nf_layer_snapshot_read.argtypes=[C.c_void_p,C.c_uint,C.c_void_p];d.nf_layer_snapshot_destroy.argtypes=[C.c_void_p];d.nf_storage_profile_read.argtypes=[C.c_void_p]
raw=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/layer-hash-candidate-20261007/actual-storage-rows.bin').read_bytes();rows=[raw[i*100480:(i+1)*100480] for i in range(160)];s=d.nf_layer_snapshot_create();d.nf_storage_profile_reset()
try:
 for row in rows:assert d.nf_layer_snapshot_add(s,C.create_string_buffer(row,len(row)))
 out=C.create_string_buffer(100480)
 for i,row in enumerate(rows):assert d.nf_layer_snapshot_read(s,i,out) and out.raw==row
 stats=(C.c_uint64*12)();d.nf_storage_profile_read(stats);results={name:dict(calls=stats[i*3],wall_ms=stats[i*3+1]/1e6,cycles=stats[i*3+2]) for i,name in enumerate(['previous_compare','page_hash','stored_page_search','store_copy_allocation'])}
finally:d.nf_layer_snapshot_destroy(s)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/layer-hash-candidate-20261007');(cp/'actual-storage-profile.json').write_text(json.dumps(dict(result='PASS_FULL_ROW_RECONSTRUCTION',stages=results,scope='One actual160rowcapture; diagnostic instrumentation overhead included in every stage, not exclusive uninstrumented costs/livebenefit'),indent=2));print(json.dumps(results,indent=2))
