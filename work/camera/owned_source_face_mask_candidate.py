"""Private source face/rectangle mask packing for synchronous GPU candidate."""
import ctypes as C,math,os
_stage_trace=None
if os.environ.get("NFSUG_SOURCE_MASK_STAGE_TRACE")=="1":
 import owned_source_mask_stage_trace as _stage_trace
from owned_model_key_records_candidate import records
from functools import lru_cache
@lru_cache(maxsize=64)
def mask_buffer_types(offset_count,face_count):
 if not 1<=offset_count<=145 or not 0<=face_count<=32768:raise ValueError('Invalid source mask buffer dimensions')
 return C.c_uint32*offset_count,C.c_uint8*max(1,face_count)


def build_source_face_mask(frame,models,bounds,alpha,classifiers):
 started=_stage_trace.begin() if _stage_trace else None
 rows=records(frame)['records']
 if _stage_trace:_stage_trace.end('record_decode',started)
 _validation_started=_stage_trace.begin() if _stage_trace else None
 if len(rows)>144 or len(models)!=12*len(rows) or len(bounds)!=4*len(rows):raise ValueError('Invalid source mask dimensions')
 if not math.isfinite(alpha) or not 0<=alpha<=1 or not all(math.isfinite(x) for x in (*models,*bounds)):raise ValueError('Invalid source mask values')
 if _stage_trace:_stage_trace.end('dimension_value_validation',_validation_started)
 offsets=[0];mask=[];rejected=0
 for position,row in enumerate(rows):
  if row['kind']==3:
   if row['key'] not in classifiers:raise ValueError('Unpaired model classification')
   started=_stage_trace.begin() if _stage_trace else None
   classifier=classifiers[row['key']];matrix=tuple(models[position*12:position*12+12]);b=bounds[position*4:position*4+4];rect=(b[0],b[2],b[1],b[3])
   faces,cl=classifier.combined_decisions(matrix,alpha,rect) if hasattr(classifier,'combined_decisions') else (classifier.decisions(matrix,alpha),classifier.rectangle_decisions(matrix,alpha,rect))
   if _stage_trace:_stage_trace.end('classify_model',started)
   started=_stage_trace.begin() if _stage_trace else None
   rejected+=sum(visible and code==4 for visible,code in zip(faces,cl));mask.extend(visible and code!=4 for visible,code in zip(faces,cl))
   if _stage_trace:_stage_trace.end('append_face_decisions',started)
  offsets.append(len(mask))
 if len(mask)>32768:raise ValueError('Source mask capacity exceeded')
 started=_stage_trace.begin() if _stage_trace else None
 offset_type,mask_type=mask_buffer_types(len(offsets),len(mask))
 result=offset_type(*offsets),mask_type(*mask),len(mask),dict(rectangle_rejected_faces=rejected,selected_faces=sum(mask))
 if _stage_trace:_stage_trace.end('pack_native_buffers',started)
 return result
