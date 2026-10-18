import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_endpoint_road_selection import endpoint_road_span_candidates
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);reference=json.loads(Path('work/camera/owned-road-region-identity-tests.json').read_text());d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nf_road_scratch_create.restype=C.c_void_p;d.nf_road_scratch_destroy.argtypes=[C.c_void_p];d.nf_road_source_runs.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p];ct=(C.c_uint32*32768)(*table);scratch=d.nf_road_scratch_create();checks=[]
try:
 for f,expected in zip(r['wall_diagnostic_frames'],reference['checks']):
  c=ClosedGraph.decode(Path(f['graph']).read_bytes());m=ClosedSceneMemory(c,rom);candidates=endpoint_road_span_candidates(c,m,road_candidates(c,m),table,include_empty=True);actual=[];details=[];state=c.graph.context[:256]
  for item in candidates:
   x=item['source'];mat=bytearray(48);struct.pack_into('<HHI',mat,36,struct.unpack_from('<H',x.material,26)[0],struct.unpack_from('<H',x.material,10)[0],struct.unpack_from('<I',state)[0]+struct.unpack_from('<I',x.material,4)[0]);bounds=(C.c_uint16*4)(*item['bounds']);uv=(C.c_uint32*2)(*(v&0xffffffff for v in struct.unpack_from('<hh',x.animation,4)));out=(C.c_uint32*(8192*17))();n=C.c_uint();missing=C.c_uint64()
   ok=d.nf_road_source_runs(scratch,x.vertices,len(x.vertices),x.offsets,len(x.offsets),x.face,bytes(mat),len(x.vertices)//68,item['affine'],c.graph.context[256:304],bounds,struct.unpack_from('<I',state,108)[0],item['input_count'],ct,struct.unpack_from('<I',c.graph.context,304)[0],item['orientation'],uv,out,8192,C.byref(n),C.byref(missing))
   key=(item['descriptor'],item['ordinal'],tuple(item['bounds']))
   if ok and not missing.value:actual.append(key)
   details.append(dict(descriptor=x.descriptor,ok=ok,runs=n.value,missing=missing.value))
  wanted=[(x['descriptor'],x['ordinal'],tuple(x['bounds'])) for x in expected['roads']];checks.append(dict(refresh=c.refresh,exact=actual==wanted,actual=actual,wanted=wanted,details=details))
finally:d.nf_road_scratch_destroy(scratch)
assert len(checks)==16 and all(x['exact'] for x in checks), 'Raw road submission mismatch'
out=dict(result='PASS_RAW_ROAD_SUBMISSION',checks=checks,exact_endpoints=sum(x['exact'] for x in checks),scope='Recovered raw source-run submission with persistent scratch; no captured draw geometry inputs')
Path('work/camera/raw-road-submission-audit.json').write_text(json.dumps(out,indent=2));print(out['result'],out['exact_endpoints']);print([(x['refresh'],x['actual'],x['wanted']) for x in checks if not x['exact']][:2])
