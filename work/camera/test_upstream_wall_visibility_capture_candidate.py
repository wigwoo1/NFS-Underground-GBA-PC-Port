import sys,json,hashlib,struct
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0];exec(compile(setup,'saved_scene_setup','exec'))
import owned_wall_visibility_candidate as target
from owned_continuous_wall_visibility import select_wall
original=target.batch;captured=[];phase=None;aliases=[]
def batch(calls):
 calls=tuple(calls);result=original(calls);assert len(result)==len(calls)
 assert len(captured)+len(calls)<=20000
 for call,actual in zip(calls,result):
  wall,descriptor,edge,fb,bounds,base,reciprocal=call
  reference=select_wall(*call)
  assert (actual.visible,actual.reason,actual.flags)==(reference.visible,reference.reason,reference.flags)
  assert len(actual.x)==len(reference.x) and len(actual.y)==len(reference.y)
  assert all(abs(x-y)<1e-9 for x,y in zip((*actual.x,*actual.y),(*reference.x,*reference.y)))
  captured.append(dict(alpha=phase,descriptor=wall.descriptor,edge_index=wall.edge,source_address=wall.address,vertices=bytes(wall.vertices).hex(),offsets=bytes(wall.offsets).hex(),framebuffer=bytes(fb).hex(),base_material=bytes(base).hex(),edge_camera=list(edge),region_bounds=list(bounds),reciprocal_sha256=hashlib.sha256(struct.pack('<'+str(len(reciprocal))+'I',*reciprocal)).hexdigest(),decision=dict(visible=actual.visible,reason=actual.reason,x=list(actual.x),y=list(actual.y),flags=actual.flags)))
 return result
for name,module in list(sys.modules.items()):
 if name=='__main__' or module is None:continue
 for key,value in list(vars(module).items()):
  if value is original:setattr(module,key,batch);aliases.append((name,key))
assert aliases
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 samples=[]
 for item in expected:
  phase=item['alpha'];before=len(captured);frame,camera,models,bounds,detail=prepared.sample(phase)
  position=40;end=40+struct.unpack_from('<I',frame,8)[0];view=0;linked=[]
  while position<end:
   magic,kind,context,count=struct.unpack_from('<4I',frame,position);position+=16;assert magic==0x3147534e and count==12;blocks=[]
   for _ in range(12):size=struct.unpack_from('<I',frame,position)[0];position+=4;blocks.append(frame[position:position+size]);position+=size
   if kind==2:
    candidates=[r for r in captured[before:] if r['decision']['visible'] and bytes.fromhex(r['vertices'])[:68]==blocks[0][:68] and bytes.fromhex(r['offsets'])[:32]==blocks[1][:32]]
    assert candidates,(phase,view)
    linked.append(dict(view_index=view,source_sha256=hashlib.sha256(blocks[0]).hexdigest(),candidate_sources=[dict(descriptor=r['descriptor'],edge_index=r['edge_index'],source_address=r['source_address']) for r in candidates],sampled_bounds=list(bounds[view*4:view*4+4])))
   view+=1
  assert position==end
  samples.append(dict(alpha=phase,calls=len(captured)-before,frame_sha256=hashlib.sha256(frame).hexdigest(),linked_walls=linked))
finally:
 if prepared is not None:prepared.close()
 history.close()
assert captured and all(r['calls'] for r in samples)
out=dict(result='PASS_CAPTURED_UPSTREAM_WALL_VISIBILITY_NATIVE_PYTHON_PARITY',samples=samples,calls=len(captured),aliases=aliases,rows=captured,scope='Saved complete scene pair replay. Actual upstream original material/region/framebuffer/edge inputs, all decisions checked against recovered Python rules. Not live pixel linkage, original ROM selection equivalence or cadence proof.')
Path('work/camera/prototype-runs/upstream-wall-visibility-20261009.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
