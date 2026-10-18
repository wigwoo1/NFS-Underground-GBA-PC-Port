"""Candidate source-matrix residuals for paired rigid model motion.

Preserves original raw camera/object matrix endpoints without screen coordinates.
Does not change discrete model textures or the default motion pipeline.
"""
import ctypes as C,math,struct,time
from owned_thread_cycles import read as thread_cycles
from owned_model_key_records_candidate import records
from sample_owned_motion import Point

class SourceModelAnchors:
 def __init__(self,motion,preanchored_keys=()):
  plan,d,ca,cb,objects,basis=motion.arguments
  pairs=dict(plan['pairs']);self.offsets={};self.raw={};self.preanchored_keys=frozenset(preanchored_keys)
  for index,oa,ob in objects:
   if plan['older']['records'][index]['key'] in self.preanchored_keys:continue
   if index not in pairs:raise ValueError('Model anchor requires paired source topology')
   older=plan['older']['records'][index];newer=plan['newer']['records'][pairs[index]]
   if older['key']!=newer['key'] or older['key'] in self.offsets:raise ValueError('Ambiguous paired model anchor')
   residuals=[];raws=[]
   for alpha,row in ((0,older),(1,newer)):
    out=(Point*4)()
    if not d.nf_rigid_scene_sample(C.byref(ca),C.byref(cb),C.byref(oa),C.byref(ob),alpha,basis,4,out):raise ValueError('Cannot sample model anchor endpoint')
    rigid=[getattr(out[col+1],name)-getattr(out[0],name) for col in range(3) for name in ('x','y','z')]+[out[0].x,out[0].y,out[0].z]
    values=struct.unpack('<12i',row['blocks'][2]);raw=tuple(v/16384 if i<9 else float(v) for i,v in enumerate(values))
    if not all(math.isfinite(v) for v in rigid):raise ValueError('Nonfinite rigid endpoint')
    residuals.append(tuple(v-w for v,w in zip(raw,rigid)));raws.append(raw)
   self.offsets[older['key']]=tuple(residuals);self.raw[older['key']]=tuple(raws)
 def sample(self,frame,models,alpha,trace=None):
  if trace is not None:
   begin=time.perf_counter_ns();cycles=thread_cycles()
   def mark(name):
    nonlocal begin,cycles
    end=time.perf_counter_ns();last=thread_cycles();trace.append(dict(name=name,started_ns=begin,completed_ns=end,wall_ns=end-begin,thread_cycles=last-cycles));begin=end;cycles=last
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid model anchor fraction')
  metadata_trace=[] if trace is not None else None
  rows=records(frame,metadata_trace)['records']
  if trace is not None:
   mark('record_metadata');trace[-1]['metadata_stages']=metadata_trace
  if len(models)!=12*len(rows) or not all(math.isfinite(v) for v in models):raise ValueError('Invalid sampled model array')
  if trace is not None:mark('finite_validation')
  buffer_type=C.c_double*len(models)
  result=buffer_type.from_buffer_copy(models) if isinstance(models,C.Array) and models._type_ is C.c_double else buffer_type(*models)
  if trace is not None:mark('private_model_copy')
  for index,row in enumerate(rows):
   if row['kind']!=3 or row['key'] in self.preanchored_keys:continue
   if row['key'] not in self.offsets:raise ValueError('Unpaired sampled model topology')
   a,b=self.offsets[row['key']]
   for k in range(12):result[index*12+k]+=(1-alpha)*a[k]+alpha*b[k]
  if trace is not None:mark('anchor_residuals')
  return result
