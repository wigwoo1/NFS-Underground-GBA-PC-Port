"""Diagnostic owner correspondence; reads known root owners without retaining them."""
import gc,time,json
from pathlib import Path
import owned_native_source_segmented_release_worker_candidate as worker
Session=worker.NativeSourceWorker._run.__globals__['NativeSourceSession'];original=Session.prepare
rows=[];count=0
def capture():
 objects=gc.get_objects();scenes=[];chains=[];roots=[]
 for obj in objects:
  kind=type(obj).__module__+'.'+type(obj).__qualname__
  if kind=='owned_motion_scene.MotionScene':scenes.append(obj)
  elif kind=='owned_resume_scene_chain.ResumeSceneChain':chains.append(obj)
  elif hasattr(type(obj),'__dict__') and type(obj).__module__.startswith(('owned_','live_')) and type(obj) not in (type,):
   attrs=getattr(obj,'__dict__',None)
   if type(attrs) is dict:
    links=[]
    for key,value in list(attrs.items()):
     vk=type(value).__module__+'.'+type(value).__qualname__
     if vk in ('owned_motion_scene.MotionScene','owned_resume_scene_chain.ResumeSceneChain'):links.append(dict(attribute=key,type=vk,identity=list(value.identity) if vk.endswith('MotionScene') else None))
     elif type(value) in (tuple,list) and len(value)<=16:
      nested=[list(x.identity) for x in value if type(x).__module__+'.'+type(x).__qualname__=='owned_motion_scene.MotionScene']
      if nested:links.append(dict(attribute=key,scene_identities=nested))
    if links:roots.append(dict(owner=kind,links=links))
 identities=[list(x.identity) for x in scenes]
 chainrows=[dict(capacity=x.capacity,identities=[list(k) for k in x.items],size=len(x.items)) for x in chains]
 refs=[]
 for scene in scenes[:12]:
  direct=gc.get_referrers(scene);descriptions=[]
  for ref in direct:
   if ref is objects or ref is scenes:continue
   if type(ref) is dict:descriptions.append(dict(type='dict',keys=[str(k) for k,v in list(ref.items()) if v is scene][:6]))
   elif type(ref) is tuple:descriptions.append(dict(type='tuple',length=len(ref),element_types=[type(v).__module__+'.'+type(v).__qualname__ for v in ref[:3]]))
  refs.append(dict(identity=list(scene.identity),direct_owners=descriptions[:12]));del direct
 del objects,scenes,chains,obj,scene
 rows.append(dict(prepare_count=count,identities=identities,chains=chainrows,known_roots=roots[:24],direct=refs))
def prepare(self,*args,**kwargs):
 global count
 result=original(self,*args,**kwargs);count+=1
 if count in (300,600):capture()
 return result
Session.prepare=prepare
def save():
 out=dict(result='DIAGNOSTIC_ACTIVE_SCENE_OWNER_CORRESPONDENCE',rows=rows,scope='Known source root identities and bounded direct referrers at2active snapshots. Diagnostic locals may appear, no object references retained; no cadence/leak proof.')
 p=Path('work/camera/prototype-runs')/('scene-owner-paths-'+str(time.time_ns())+'.json');p.write_text(json.dumps(out,indent=2));print('SCENE_OWNER_MANIFEST',p,flush=True)
