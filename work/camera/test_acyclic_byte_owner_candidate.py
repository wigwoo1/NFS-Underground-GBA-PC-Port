import ctypes as C,weakref,gc,json
from pathlib import Path
rows=[]
for mode in ('cast','from_buffer'):
 owner=C.c_char_p(b'owned immutable frame');ref=weakref.ref(owner);expected=C.c_void_p.from_buffer(owner).value
 pointer=C.cast(owner,C.c_void_p).value if mode=='cast' else C.c_void_p.from_buffer(owner).value
 assert pointer==expected and C.string_at(pointer)==b'owned immutable frame'
 kind=type(owner._objects).__name__;del owner;alive=ref() is not None
 gc.collect();assert ref() is None
 rows.append(dict(mode=mode,owner_objects_type=kind,retained_until_collection=alive))
assert not any(x['retained_until_collection'] for x in rows)
Path('work/camera/prototype-runs/acyclic-byte-owner-component-20261009.json').write_text(json.dumps(dict(rows=rows,result='BYTE_OWNER_CYCLE_HYPOTHESIS_REJECTED'),indent=2));print(rows)
