"""Render every slot on the existing original-cycle/60Hz schedule."""
from owned_motion_clock import scene_samples
from owned_source_draw_context_candidate import OwnedSourceDraw
class NativeSourceInterval:
 def __init__(self,commit):self.commit=commit
 def render(self,pair,asset,boundaries,origin,base,older,newer,delay,epoch,generation,diagnostic=False):
  results=[]
  for slot in scene_samples(origin,base,older,newer,delay):
   alpha=slot['alpha'];frame,camera,models,bounds,detail=pair.sample(alpha);offsets,mask,total,_=pair.source_masks[alpha]
   owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*pair.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
   row=self.commit.run(owned,epoch,generation,older,newer,slot['index'],alpha,slot['deadline_ns'],diagnostic=diagnostic);row['slot']=slot;results.append(row)
   if row['native_result']==0:break
  return results
