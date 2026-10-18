import runpy,ctypes as C,hashlib,struct
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_scenery_record_pairs import prepare_scenery_record_pairs
import owned_scenery_record_pairs as owners
from owned_motion_pairs import records
from owned_sampled_supplemental_frame import encode
v=runpy.run_path('work/camera/audit_failed_world_motion.py');h=EndpointRoadPlanner(v['rom'],v['data']['table']);roads,_=h.plan(v['scenes'][0].graph);direct=PreparedWorldMotion(*v['data']['frames'],*v['scenes'],h,roads,v['rom']);reference=None;original=owners.captured_scenery_record_pairs
alphas=(0,.1,.25,.5,.75,.9,.99,1)
def digest(sample):
 value=hashlib.sha256(sample[0])
 for raw in sample[1:4]:
  if raw is not None:value.update(C.string_at(C.addressof(raw),C.sizeof(raw)))
 return value.hexdigest()
try:
 expected=[digest(direct.sample(a)) for a in alphas]
 owners.captured_scenery_record_pairs=lambda scenes,queues,frames,maps,rom,indices:prepare_scenery_record_pairs(scenes,queues,rom,indices)
 reference=PreparedWorldMotion(*v['data']['frames'],*v['scenes'],h,roads,v['rom']);assert [digest(reference.sample(a)) for a in alphas]==expected
 frame=v['data']['frames'][1];rows=records(frame)['records'];maps=direct.pair._model_record_owners;index=next(i for i,owner in maps[1].items() if owner==33);blocks=list(rows[index]['blocks']);raw=bytearray(blocks[2]);raw[0]^=1;blocks[2]=bytes(raw);rows[index]=dict(rows[index],blocks=blocks);g=b''.join(encode(row) for row in rows);head=list(struct.unpack_from('<6I2Q',frame));tail=frame[40+head[2]:];head[2]=len(g);bad=struct.pack('<6I2Q',*head)+g+tail
 try:original(v['scenes'],[direct.pair.portal.sample(i) for i in (0,1)],(v['data']['frames'][0],bad),maps,v['rom'],{33});raise AssertionError('Unowned modified pose accepted')
 except ValueError as error:assert 'pose/source mismatch' in str(error),error
 print('PASS eight complete scene/pose/clip samples equal original reconstruction and modified source pose rejected')
finally:
 owners.captured_scenery_record_pairs=original;direct.close();h.close()
 if reference:reference.close()
