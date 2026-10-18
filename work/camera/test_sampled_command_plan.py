"""Structural native plan versus independent sampled ARM draw traces."""
from pathlib import Path
import ctypes as C,json,struct,copy
p=Path('work/camera');d=C.CDLL(str((p/'sampled-command-plan-test.dll').resolve()))
fn=d.nf_sampled_command_plan;fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
def packed(rows):return b''.join(struct.pack('<'+'I'*len(row),*row) for row in rows)
def evaluate(queue,calls,draws,success):
 output=C.create_string_buffer(b'X'*(4+256*40),4+256*40)
 ci=packed([list(struct.unpack('<4I',struct.pack('<8H',*c['record'])))+[c[k] for k in ('caller','pass_index','begin','end','depth','object')] for c in calls])
 di=packed([({'road':1,'wall':2,'model':3}[v['kind']],v['source'],v['owner']) for v in draws])
 ok=fn(queue,len(queue)//16,ci,len(calls),di,len(draws),output)
 assert bool(ok)==success
 if not success:assert output.raw==b'X'*len(output);return
 roots=[(qi,phase,queue[qi*16:qi*16+16]) for phase in (0,1) for qi in reversed(range(len(queue)//16)) if not struct.unpack_from('<H',queue,qi*16+10)[0]&(0x88 if phase else 8)]
 rootmap={};stack=[];ri=0
 for i,c in enumerate(calls):
  stack=stack[:c['depth']]
  if not stack:rootmap[i]=roots[ri][0];ri+=1
  else:rootmap[i]=rootmap[stack[-1]]
  stack.append(i)
 expected=[]
 for v in draws:
  c=calls[v['owner']];expected.append([{'road':1,'wall':2,'model':3}[v['kind']],v['source'],v['source'] if v['kind']=='model' else c['object'],v['owner'],rootmap[v['owner']],c['pass_index'],*struct.unpack('<4I',struct.pack('<8H',*c['record']))])
 assert struct.unpack_from('<I',output.raw)[0]==len(expected)
 assert [list(struct.unpack_from('<10I',output.raw,4+i*40)) for i in range(len(expected))]==expected
 return expected
cases=[];rejections=0
for alpha in ('0.25','0.5','0.75'):
 r=json.loads((p/f'sampled-object-dispatch-{alpha}-tests.json').read_text());raw=(p/f'visibility-overflow-171-wide/result-{alpha}.bin').read_bytes();queue=raw[256:256+r['queue_count']*16]
 plan=evaluate(queue,r['calls'],r['draws'],True)
 assert sum(v[0]==1 and v[1]==139900368 for v in plan)==1
 assert sum(v[0]==3 for v in plan)==1
 (p/f'sampled-command-plan-{alpha}.json').write_text(json.dumps(dict(alpha=float(alpha),commands=plan,fields=['kind','source','object','owner','queue_index','pass','record0','record1','record2','record3']),indent=2))
 cases.append(dict(alpha=float(alpha),commands=len(plan),model_queue_indices=[v[4] for v in plan if v[0]==3],object_surface_commands=sum(bool(v[2]) and v[0]!=3 for v in plan)))
 # Negative cases alter independent structure, not renderer pixel behavior.
 for mode in ('root_record','child_bounds','child_caller','child_object','draw_owner','draw_kind','root_missing'):
  calls=copy.deepcopy(r['calls']);draws=copy.deepcopy(r['draws']);child=next(i for i,c in enumerate(calls) if c['caller']==0x03002364)
  if mode=='root_record':calls[0]['record'][1]^=1
  elif mode=='child_bounds':calls[child]['end']=len(draws)+1
  elif mode=='child_caller':calls[child]['caller']=0x03000000
  elif mode=='child_object':calls[child]['object']=0
  elif mode=='draw_owner':next(v for v in draws if v['owner']==child)['owner']=child-1
  elif mode=='draw_kind':draws[0]['kind']='model';draws[0]['source']=0
  elif mode=='root_missing':calls.pop()
  evaluate(queue,calls,draws,False);rejections+=1
report=dict(result='PASS',cases=cases,atomic_rejections=rejections,scope='Native structural binding from offline original eligibility/draw traces. Does not generate eligibility, geometry, materials, contexts or pixels; not integrated live.')
(p/'sampled-command-plan-tests.json').write_text(json.dumps(report,indent=2));print(report)
