import sys,json,ctypes as C,time,statistics
from pathlib import Path
from unittest.mock import patch
setup=Path('work/camera/benchmark_road_decode_full_scene.py').read_text().split('import statistics')[0];exec(compile(setup,'actual_capture_setup','exec'))
import owned_prepared_world_motion as assembly
import owned_road_decode_candidate as candidate
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None
try:
 with patch.object(assembly,'SampledRoadSequence',candidate.SampledRoadSequence):prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 original=candidate.clipped_camera_road;seen=[]
 def mutate_after(*args,**kwargs):
  result=original(*args,**kwargs);attrs=args[3];seen.append(bytes(attrs));C.memset(C.addressof(attrs),255,C.sizeof(attrs));return result
 with patch.object(candidate,'clipped_camera_road',mutate_after):
  for row in expected:
   sample=prepared.sample(row['alpha']);assert json.loads(json.dumps(signature(sample)))==row['signature']
  first=[(k,v[1]) for k,v in prepared.roads._decoded_sources.items()]
  for row in expected:
   sample=prepared.sample(row['alpha']);assert json.loads(json.dumps(signature(sample)))==row['signature']
 assert first==[(k,v[1]) for k,v in prepared.roads._decoded_sources.items()];assert len(first)<=64;assert seen
 # Actual native decode repeated on one immutable source versus fresh attributes copy.
 source=prepared.roads.sources[0];n=len(source.vertices)//68;mat=bytearray(48);struct.pack_into('<HH',mat,36,struct.unpack_from('<H',source.material,26)[0],struct.unpack_from('<H',source.material,10)[0]);world=(C.c_double*96)();attrs=candidate.Attributes();d=history.d
 d.nf_road_source_decode.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
 def decode_once():
  assert d.nf_road_source_decode(source.vertices,len(source.vertices),source.offsets,len(source.offsets),source.face,bytes(mat),n,0,world,C.byref(attrs))
  return tuple(world)[:n*3],bytes(attrs)
 raw,encoded=decode_once();times={'decode':[],'copy':[]}
 for trial in range(10):
  for name in (('decode','copy') if trial%2==0 else ('copy','decode')):
   begin=time.perf_counter_ns()
   for i in range(1000):
    if name=='decode':value=decode_once();assert value==(raw,encoded)
    else:copy=candidate.Attributes.from_buffer_copy(encoded);assert bytes(copy)==encoded
   times[name].append((time.perf_counter_ns()-begin)/1e6)
 out=dict(result='PASS_PRIVATE_ATTRIBUTES_COMPLETE_SIGNATURES',sample_checks=2*len(expected),cached_sources=len(first),attribute_mutations=len(seen),component_1000_median_ms={k:statistics.median(v) for k,v in times.items()},scope='Actual captured road source native decode vs private attributes copy; excludes cache lookup/whole-scene timing/GPU/live')
 Path('work/camera/road-decode-private-attributes-tests.json').write_text(json.dumps(out,indent=2));print(out)
finally:
 if prepared is not None:prepared.close()
 history.close()
