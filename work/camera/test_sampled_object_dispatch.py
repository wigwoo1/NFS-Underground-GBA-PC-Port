"""Original sampled scene ordering and shared native object visitation oracle."""
from pathlib import Path
import json,struct,sys,ctypes as C,hashlib
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
p=Path('work/camera');f=p/'visibility-overflow-171-wide';rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();ew=(f/'ewram.bin').read_bytes();iw=(f/'iwram.bin').read_bytes();alpha=sys.argv[1] if len(sys.argv)>1 else '0.5';meta=json.loads((f/f'sample-{alpha}.json').read_text());address=meta['state_address'];result=(f/f'result-{alpha}.bin').read_bytes();pose=(f/f'pose-{alpha}.bin').read_bytes()

count=struct.unpack_from('<H',result,238)[0]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for base,size in ((0x02000000,0x40000),(0x03000000,0x10000),(0x04000000,0x10000),(0x05000000,0x1000),(0x06000000,0x20000),(0x08000000,0x800000)):u.mem_map(base,size)
model_inputs=(p/'overflow-scene-171/model-inputs.bin').read_bytes();assert len(model_inputs)==560
u.mem_write(0x05000000,model_inputs[48:]);u.mem_write(0x02000000,ew);u.mem_write(0x03000000,iw);u.mem_write(0x08000000,rom);u.mem_write(address,result[:256]);u.mem_write(struct.unpack_from('<I',result,84)[0],pose[56:104]);u.mem_write(0x04001000,result[256:256+count*16]);u.mem_write(address+0x60,struct.pack('<I',0x04001000));u.mem_write(address+0xee,struct.pack('<H',count))
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nfs_visibility_object_visit;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_void_p,C.c_void_p]
motion=len(sys.argv)>2 and sys.argv[2]=='motion';suffix='-motion' if motion else '';sampled_object_pose=None
road_full=len(sys.argv)>3 and sys.argv[3]=='road-full'
road_writes=len(sys.argv)>3 and sys.argv[3] in ('road-writes','road-full')
road_edges=len(sys.argv)>3 and sys.argv[3]=='road-edges'
road_plan=len(sys.argv)>3 and sys.argv[3]=='road-plan'
road_spans=len(sys.argv)>3 and sys.argv[3] in ('road-spans','road-writes','road-edges','road-plan','road-full')
if road_spans:suffix+='-writes' if road_writes else '-spans'
if road_full:suffix+='-full';full_pending=[];full_checks=[];full_atomic=[]
if road_plan:
 suffix+='-plan';plan_library=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));plan_fn=plan_library.nf_road_span_plan
 plan_fn.argtypes=[C.c_void_p,C.c_uint,C.c_int32,C.c_int32,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
 plan_reciprocal=C.create_string_buffer(rom[0x627700:0x647700])
if road_edges:
 suffix+='-edges';edge_pending=[];edge_checks=[]
 edge_library=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));edge_fn=edge_library.nf_road_edge_step
 edge_fn.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
 edge_reciprocal=C.create_string_buffer(rom[0x627700:0x647700])
road_clips=road_full or (len(sys.argv)>3 and sys.argv[3]=='road-clips')
if road_clips:
 if not road_full:suffix+='-clips'
 clip_library=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));clip_fn=clip_library.nf_road_polygon_clip
 clip_fn.argtypes=[C.c_void_p,C.c_uint,C.c_int32,C.c_int32,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
 clip_reciprocal=C.create_string_buffer(rom[0x627700:0x647700]);clip_expected=None;clip_checks=[]
if motion:
 def model_section(packet):
  return next(packet[o:o+n] for tag,o,n in (struct.unpack_from('<3I',packet,32+i*12) for i in range(5)) if tag==1)
 packet_a=(p/'overflow-scene-171/old.bin').read_bytes();packet_b=(p/'overflow-scene-171/new.bin').read_bytes();model_a=model_section(packet_a);model_b=model_section(packet_b)
 def model_identity(packet):
  ids=next(packet[o:o+n] for tag,o,n in (struct.unpack_from('<3I',packet,32+i*12) for i in range(5)) if tag==5)
  return struct.unpack_from('<5I',ids,len(ids)-20)
 ident=model_identity(packet_a);assert ident==model_identity(packet_b) and ident[0]==3
 object_address=ident[2];object_record=bytes(u.mem_read(object_address,164));sampled=C.create_string_buffer(164);rotation=C.create_string_buffer(48)
 sample=d.nf_object_pose_sample;sample.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p]
 assert sample(object_record,model_a[104:160],model_b[104:160],float(alpha),sampled,rotation)
 assert sampled.raw[:12]==object_record[:12] and sampled.raw[24:]==object_record[24:]
 u.mem_write(object_address,sampled.raw);model_inputs=rotation.raw+model_inputs[48:]
 sampled_object_pose=list(struct.unpack_from('<3i',sampled.raw,12))
region_entry_inputs=[];calls=[];models=[];visits=[];active=[];pending=[];verified=[];draws=[];contexts=[];context_pending=[];model_payloads=[];object_surfaces=[];road_clip_inputs=[]
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@Read
def read(ctx,a,out,n):
 try:C.memmove(out,bytes(u.mem_read(a,n)),n);return 1
 except Exception:return 0
extract=d.nf_extract_model;extract.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_void_p,C.c_void_p];d.nf_surface_free.argtypes=[C.c_void_p]
wall=d.nf_extract_wall_candidate_diagnostic;wall.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
context_fn=d.nfs_visibility_object_model_context;context_fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p]
if road_writes:
 pixel_library=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));pixel_fn=pixel_library.nf_road_span_pixels;pixel_fn.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_uint];pixel_pending=[];pixel_checks=[]
 perspective_fn=pixel_library.nf_road_perspective_plan;perspective_fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p];perspective_reciprocal=C.create_string_buffer(rom[0x627700:0x647700]);perspective_pending=[];perspective_checks=[]
 if road_full:
  contexts_fn=pixel_library.nf_road_span_contexts;contexts_fn.argtypes=[C.c_void_p,C.c_uint,C.c_int32,C.c_int32,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
  bounds_fn=pixel_library.nf_road_clip_bounds;bounds_fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
  collection_gate_fn=d.nfs_visibility_region_object_gate;collection_gate_fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Read,C.c_void_p,C.c_void_p];collection_gate_predictions=[];collection_gate_actual=[];entry_source_plans={};combined_checks=[]
  combined_fn=d.nfs_visibility_region_object_plan;combined_fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
  sources_fn=d.nfs_visibility_object_sources;sources_fn.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];source_predictions=[];source_actual=[];source_checks=[]
  sort_fn=d.nfs_visibility_object_sort;sort_fn.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];sort_pending=[];sort_checks=[]
  object_region_fn=d.nfs_visibility_object_region_prepare;object_region_fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];object_region_pending=[];object_region_predictions=[];object_region_actual=[];object_region_checks=[]
  static_fn=d.nfs_visibility_static_child_record;static_fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Read,C.c_void_p,C.c_void_p,C.c_void_p];static_predictions=[];static_actual=[]
  reconstruct_fn=d.nfs_visibility_region_reconstruct;reconstruct_fn.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];geometry_checks=[]
  seed_fn=pixel_library.nf_road_material_seed;seed_fn.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p];seed_checks=[]
class NativeCursor(C.Structure):_fields_=[('current',C.c_uint32),('count',C.c_uint32),('seen',C.c_uint8*512)]
class NativeCollector(C.Structure):_fields_=[('cursor',NativeCursor),('awaiting_callback',C.c_uint)]
class NativeAction(C.Structure):_fields_=[('kind',C.c_uint32),('pass_index',C.c_uint32),('mask',C.c_uint32),('record',C.c_uint8*16)]
class NativeSource(C.Structure):_fields_=[('region',C.c_uint32),('head',C.c_uint32)]
class NativeDispatch(C.Structure):_fields_=[('sources',NativeSource*512),('count',C.c_uint),('next',C.c_uint),('object_count',C.c_uint),('collector',NativeCollector)]
class NativeDelta(C.Structure):_fields_=[('offset',C.c_uint32),('before',C.c_uint32),('after',C.c_uint32)]
if road_full:
 collector_begin=d.nfs_visibility_object_cursor_begin;collector_begin.argtypes=[C.c_void_p,C.c_uint,C.c_uint]
 collector_step=d.nfs_visibility_object_collect_step;collector_step.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
 collector_apply=d.nfs_visibility_object_callback_apply;collector_apply.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
 dispatch_begin=d.nfs_visibility_object_dispatch_begin;dispatch_begin.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint]
 dispatch_next=d.nfs_visibility_object_dispatch_next;dispatch_next.argtypes=[C.c_void_p,C.c_void_p];dispatch_jobs={};dispatch_checks=[]
 sorted_plan=d.nfs_visibility_object_sorted_plan;sorted_plan.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p];sorted_plan_checks=[]
 branch_prepare=d.nfs_visibility_object_branch_prepare;branch_prepare.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];branch_pending=[];branch_checks=[]
 material_plan=d.nfs_visibility_object_material_plan;material_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p];material_pending=[];material_checks=[]
 model_plan=d.nfs_visibility_object_model_plan;model_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p];owned_model_pending=[];owned_model_checks=[];owned_model_extract={}
 region_actions=d.nfs_visibility_region_actions;region_actions.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];action_expected={};action_actual={};action_atomic=[];action_snapshots=[];original_phase_trace=[];original_command_trace=[];original_wall_leaves=[];original_assets=[];original_lights=[];original_road_states=[];original_road_materials=[]
 collector_context={};collector_checks=[];collector_callbacks=[];original_callback_requests=[];native_sorted_draw={};native_draw_checks=[]
 def collector_resume():
  c=collector_context;selector=C.c_uint();status=collector_step(C.byref(c['owner']),c['pool'],c['bits'],32,c['matrix'],C.byref(c['head']),C.byref(c['maximum']),C.byref(selector));return status,selector.value
current_road=None;nonroad_write_pcs={}
def hook(cpu,pc,length,ctx):
 global clip_expected,current_road,native_region_state
 if road_full and pc==0x03003808:
  base,frame,span_contexts,index=full_pending.pop();assert index==len(span_contexts)
  assert bytes(cpu.mem_read(base,len(frame)))==frame,(alpha,road_clip_inputs[-1]['source'],'complete native road framebuffer')
  full_checks.append(dict(source=road_clip_inputs[-1]['source'],spans=len(span_contexts),affine=road_clip_inputs[-1]['affine'],near_clipped_edges=geometry_checks[-1]['near_clipped_edges'],changed_bytes=road_clip_inputs[-1]['changed_bytes'],frame_sha256=hashlib.sha256(frame).hexdigest()))
 if road_writes and pc==0x03003808:current_road=None
 if road_writes and pc==0x030032e4:
  pointer,expected,final,index=perspective_pending.pop();assert index==len(expected) and bytes(cpu.mem_read(pointer,64))==final
  perspective_checks.append(len(expected))
 if road_writes and pc==0x03005790:
  destination,expected,doubled=pixel_pending.pop();assert bytes(cpu.mem_read(destination,len(expected)))==expected
  if doubled:assert bytes(cpu.mem_read(destination+240,len(expected)))==expected
  pixel_checks.append(dict(samples=len(expected)//2,doubled=bool(doubled)))
 if road_edges and pc==0x03002f88:
  pointer=cpu.reg_read(UC_ARM_REG_R0);before=bytes(cpu.mem_read(pointer,72));words=struct.unpack('<18I',before)
  verts=bytes(cpu.mem_read(words[10],words[11]*24));framebuffer=bytes(cpu.mem_read(words[17],16));output=C.create_string_buffer(b'X'*72,72)
  status=edge_fn(before,cpu.reg_read(UC_ARM_REG_R1),cpu.reg_read(UC_ARM_REG_R2),verts,words[11],edge_reciprocal,framebuffer,output)
  assert status>=0
  edge_pending.append((pointer,output.raw,status))
 if road_edges and pc==0x0300317c:
  pointer,expected,status=edge_pending.pop();assert cpu.reg_read(UC_ARM_REG_R0)==status
  if status:assert bytes(cpu.mem_read(pointer,72))==expected,(alpha,[(i,a,b) for i,(a,b) in enumerate(zip(bytes(cpu.mem_read(pointer,72)),expected)) if a!=b][:10])
  else:assert expected==b'X'*72
  edge_checks.append(status)
 if road_clips and pc==0x03000efc:
  state_bytes=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),256));vertex_base=struct.unpack_from('<I',state_bytes,108)[0];amount=struct.unpack_from('<H',state_bytes,242)[0]
  original=bytes(cpu.mem_read(vertex_base,amount*24));left,right=struct.unpack_from('<2H',state_bytes,226)
  if road_full:
   entry_state,entry_edges,entry_stream=region_entry_inputs[calls.index(active[-1])]
   native_state=C.create_string_buffer(entry_state,256);edge_address=struct.unpack_from('<I',state_bytes,104)[0]
   edges=C.create_string_buffer(entry_edges,1664);stream=C.create_string_buffer(entry_stream,1536)
   assert reconstruct_fn(native_state,struct.pack('<8H',*active[-1]['record']),read,None,clip_reciprocal,edges,1664,stream,1536)==1
   assert native_state.raw==state_bytes,(alpha,active[-1]['region'],[(i,a,b) for i,(a,b) in enumerate(zip(native_state.raw,state_bytes)) if a!=b])
   emitted_native=struct.unpack_from('<H',native_state.raw,242)[0]
   assert emitted_native==amount and stream.raw[:amount*24]==original,(alpha,active[-1]['region'],'native preclip stream')
   original=stream.raw[:amount*24]
   descriptor_address=struct.unpack_from('<I',entry_state,0x14)[0]+active[-1]['region']*48
   edge_count=struct.unpack_from('<H',bytes(cpu.mem_read(descriptor_address,48)),2)[0]
   assert edge_count<=32
   near_edges=sum(bool(struct.unpack_from('<H',edges.raw,i*52+48)[0]&24) for i in range(edge_count))
   geometry_checks.append(dict(region=active[-1]['region'],vertices=amount,near_clipped_edges=near_edges))
  output=C.create_string_buffer(3072);emitted=C.c_uint();assert clip_fn(original,amount,left,right,clip_reciprocal,output,128,C.byref(emitted))
  clip_expected=(output.raw[:emitted.value*24],emitted.value,amount)
  if road_full:
   owned_state=bytearray(native_state.raw);struct.pack_into('<H',owned_state,244,emitted.value);native_region_state=bytes(owned_state)
 if road_spans and pc in (0x030056d8,0x03003190):
  if road_full and not perspective_pending:
   base,frame,span_contexts,index=full_pending[-1];native=span_contexts[index][4:];actual=struct.unpack('<16I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),64)))
   used=[0,1,2,5,6,7,8,9,10,11] if pc==0x030056d8 else [0,1,2]+list(range(4,16))
   assert all(native[i]==actual[i] for i in used),(alpha,road_clip_inputs[-1]['source'],[(i,native[i],actual[i]) for i in used if native[i]!=actual[i]])
   full_pending[-1]=(base,frame,span_contexts,index+1)
  params=list(struct.unpack('<14I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),56))))
  road_clip_inputs[-1].setdefault('spans',[]).append(dict(routine=pc,params=params,doubled=struct.unpack('<I',bytes(cpu.mem_read(0x03007098,4)))[0]))
  if road_writes and pc==0x030056d8:
   if perspective_pending:
    pointer,expected,final,index=perspective_pending[-1];assert bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),64))==expected[index]
    perspective_pending[-1]=(pointer,expected,final,index+1)
   colors=C.create_string_buffer(params[7]*2);assert pixel_fn(struct.pack('<12I',*params[:12]),read,None,colors,params[7])
   pixel_pending.append((params[6],colors.raw,road_clip_inputs[-1]['spans'][-1]['doubled']))
  if road_writes and pc==0x03003190:
   pointer=cpu.reg_read(UC_ARM_REG_R0);native=C.create_string_buffer(2048);final=C.create_string_buffer(64);n=C.c_uint()
   assert perspective_fn(bytes(cpu.mem_read(pointer,64)),perspective_reciprocal,native,32,C.byref(n),final)
   perspective_pending.append((pointer,[native.raw[i*64:(i+1)*64] for i in range(n.value)],final.raw,0))
  if not road_writes:cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR));return
 if road_full and pc==0x030054a0:
  original_phase_trace.append((calls.index(active[-1]),3,0,bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16))))
  collection_gate_actual.append(calls.index(active[-1]));action_actual[calls.index(active[-1])].append((3,0,bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16))))
  state=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),256));record=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16));plan=C.create_string_buffer(4096);amount=C.c_uint();assert sources_fn(state,record,read,None,plan,512,C.byref(amount));source_predictions.extend(struct.unpack_from('<2I',plan.raw,i*8)[1] for i in range(amount.value));source_checks.append(amount.value);assert plan.raw[:amount.value*8]==entry_source_plans[calls.index(active[-1])]
  job=NativeDispatch();assert dispatch_begin(C.byref(job),plan,amount.value,256);dispatch_jobs[calls.index(active[-1])]=job
 if road_full and pc==0x03002000:
  source_actual.append(cpu.reg_read(UC_ARM_REG_R1))
  assert not collector_context
  state=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),256));base=struct.unpack_from('<I',state,60)[0];matrix_address=struct.unpack_from('<I',state,84)[0];job=dispatch_jobs[calls.index(active[-1])];source_region=C.c_uint();assert dispatch_next(C.byref(job),C.byref(source_region))==1;owner=job.collector;assert owner.cursor.current==cpu.reg_read(UC_ARM_REG_R1);dispatch_checks.append(source_region.value)
  collector_context.update(owner=owner,base=base,matrix_address=matrix_address,pool=C.create_string_buffer(bytes(cpu.mem_read(base,256*164)),256*164),bits=C.create_string_buffer(bytes(cpu.mem_read(0x030070c0,32)),32),matrix=C.create_string_buffer(bytes(cpu.mem_read(matrix_address,48)),48),head=C.c_uint(struct.unpack('<I',bytes(cpu.mem_read(0x030070e0,4)))[0]),maximum=C.c_uint(struct.unpack('<I',bytes(cpu.mem_read(0x030070a4,4)))[0]),waiting=False,steps=0)
 if road_full and pc==0x03002020:
  c=collector_context;assert c['owner'].cursor.current==cpu.reg_read(UC_ARM_REG_R1);status,selector=collector_resume();assert status in (1,2);c['waiting']=status==2;c['selector']=selector;c['steps']+=1
 if road_full and pc==0x03002088 and collector_context.get('waiting'):
  c=collector_context;assert c['selector']==cpu.reg_read(UC_ARM_REG_R2)
  c['before_pool']=bytes(cpu.mem_read(c['base'],256*164));c['before_bits']=bytes(cpu.mem_read(0x030070c0,32));c['before_matrix']=bytes(cpu.mem_read(c['matrix_address'],48));c['before_globals']=[struct.unpack('<I',bytes(cpu.mem_read(a,4)))[0] for a in (0x030070e0,0x030070a4)]
 if road_full and pc==0x03002090 and collector_context.get('waiting'):
  c=collector_context;after=bytes(cpu.mem_read(c['base'],256*164));changes=[(i,a,b) for i,(a,b) in enumerate(zip(c['before_pool'],after)) if a!=b];deltas=(NativeDelta*len(changes))(*(NativeDelta(*v) for v in changes))
  assert collector_apply(C.byref(c['owner']),c['pool'],c['owner'].cursor.current,c['selector'],deltas,len(changes))
  for key,callback_address,n in (('bits',0x030070c0,32),('matrix',c['matrix_address'],48)):
   after=bytes(cpu.mem_read(callback_address,n));before=c['before_'+key];owned=bytearray(c[key].raw)
   for i,(a,b) in enumerate(zip(before,after)):
    if a!=b:assert owned[i]==a;owned[i]=b
   C.memmove(c[key],bytes(owned),n)
  for i,(key,callback_address) in enumerate((('head',0x030070e0),('maximum',0x030070a4))):
   value=struct.unpack('<I',bytes(cpu.mem_read(callback_address,4)))[0]
   if value!=c['before_globals'][i]:assert c[key].value==c['before_globals'][i];c[key].value=value
  assert not changes and bytes(cpu.mem_read(0x030070c0,32))==c['before_bits'] and bytes(cpu.mem_read(c['matrix_address'],48))==c['before_matrix'] and [struct.unpack('<I',bytes(cpu.mem_read(a,4)))[0] for a in (0x030070e0,0x030070a4)]==c['before_globals'],'callback not no-op; explicit delta replay required'
  original_callback_requests.append((c['owner'].cursor.current,c['selector']))
  status,selector=collector_resume();assert status==1;c['waiting']=False;collector_callbacks.append(len(changes))
 if road_full and pc in (0x030021f8,0x03002204) and collector_context:
  c=collector_context;assert c['pool'].raw==bytes(cpu.mem_read(c['base'],256*164)) and c['bits'].raw==bytes(cpu.mem_read(0x030070c0,32)) and c['head'].value==struct.unpack('<I',bytes(cpu.mem_read(0x030070e0,4)))[0] and c['maximum'].value==struct.unpack('<I',bytes(cpu.mem_read(0x030070a4,4)))[0]
  if pc==0x03002204:
   assert c['owner'].cursor.current==65535 and not c['waiting'];collector_checks.append(c['steps']);assert not native_sorted_draw or native_sorted_draw['next']==65535
   plan=(C.c_uint32*512)();amount=C.c_uint();assert sorted_plan(c['pool'],256,c['head'].value,plan,512,C.byref(amount));indices=list(plan[:amount.value]);sorted_plan_checks.append(amount.value)
   native_sorted_draw.update(base=c['base'],pool=c['pool'].raw,next=c['head'].value,seen=set(),indices=indices,position=0);collector_context.clear()
 if road_full and pc==0x03002090:
  base=struct.unpack('<I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R7)+60,4)))[0];candidate=(cpu.reg_read(UC_ARM_REG_R6)-base)//164;head=C.c_uint(struct.unpack('<I',bytes(cpu.mem_read(0x030070e0,4)))[0]);maximum=C.c_uint(struct.unpack('<I',bytes(cpu.mem_read(0x030070a4,4)))[0]);highest=candidate;node=head.value;seen=set()
  while node!=65535:
   assert node<512 and node not in seen;seen.add(node);highest=max(highest,node);node=struct.unpack('<H',bytes(cpu.mem_read(base+node*164+4,2)))[0]
  pool=C.create_string_buffer(bytes(cpu.mem_read(base,(highest+1)*164)),(highest+1)*164);matrix_pointer=struct.unpack('<I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R7)+84,4)))[0]
  status=sort_fn(pool,highest+1,candidate,bytes(cpu.mem_read(matrix_pointer,48)),C.byref(head),C.byref(maximum));assert status>=0
  sort_pending.append((base,pool.raw,head.value,maximum.value,status))
 if road_full and pc in (0x030021f8,0x03002204) and sort_pending:
  base,pool,head,maximum,status=sort_pending.pop();assert pool==bytes(cpu.mem_read(base,len(pool))) and head==struct.unpack('<I',bytes(cpu.mem_read(0x030070e0,4)))[0] and maximum==struct.unpack('<I',bytes(cpu.mem_read(0x030070a4,4)))[0];sort_checks.append(status)
 if road_full and pc==0x03002284:
  c=native_sorted_draw;assert c['position']<len(c['indices']);index=c['indices'][c['position']];c['position']+=1;assert index==c['next'];assert index!=65535 and index not in c['seen'] and cpu.reg_read(UC_ARM_REG_R7)==c['base']+index*164;c['seen'].add(index);c['next']=struct.unpack_from('<H',c['pool'],index*164+4)[0];native_draw_checks.append(index)
  state=C.create_string_buffer(bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R6),256)),256);sp=cpu.reg_read(UC_ARM_REG_SP);parent=bytes(cpu.mem_read(struct.unpack('<I',bytes(cpu.mem_read(sp+0x24,4)))[0],16));matrix=bytes(cpu.mem_read(struct.unpack('<I',bytes(cpu.mem_read(sp+0x14,4)))[0],48));xyz=(C.c_uint32*3)();branch=C.c_uint();record=C.create_string_buffer(b'X'*16,16)
  assert branch_prepare(state,c['pool'][index*164:(index+1)*164],parent,matrix,xyz,C.byref(branch),record)==1;branch_pending.append((state.raw,list(xyz),branch.value,record.raw))
 if road_full and pc==0x03002368:
  sp=cpu.reg_read(UC_ARM_REG_SP);xyz=(C.c_uint32*3)(*[struct.unpack('<I',bytes(cpu.mem_read(sp+o,4)))[0] for o in (16,12,8)]);obj_address=cpu.reg_read(UC_ARM_REG_R7);obj=C.create_string_buffer(bytes(cpu.mem_read(obj_address,164)),164);output=(C.c_uint32*4)();status=material_plan(bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R6),256)),obj,xyz,read,None,clip_reciprocal,output);assert status>=0;material_pending.append((obj_address,obj.raw,status,list(output)))
  if status==1 and output[3]==0:
   context=C.create_string_buffer(bytes(cpu.mem_read(sp+0x48,68)),68);ready=model_plan(bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R6),256)),obj,output,read,None,context);assert ready>=0;owned_model_pending.append((ready,context.raw))
 if road_full and pc in (0x03002460,0x03002588) and material_pending:
  obj_address,obj,status,output=material_pending.pop();sp=cpu.reg_read(UC_ARM_REG_SP);assert status==1 and bytes(cpu.mem_read(obj_address,164))==obj;assert output==[cpu.reg_read(UC_ARM_REG_R4),cpu.reg_read(UC_ARM_REG_R12),struct.unpack('<I',bytes(cpu.mem_read(sp+4,4)))[0],int(pc==0x03002460)];material_checks.append(output[3])
 if road_full and pc==0x0300262c and material_pending:
  obj_address,obj,status,output=material_pending.pop();assert status==0 and bytes(cpu.mem_read(obj_address,164))==obj;material_checks.append(-1)
 if road_full and pc==0x030022d8:
  state=C.create_string_buffer(bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R6),256)),256);obj=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R7),164));parent=bytes(cpu.mem_read(struct.unpack('<I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_SP)+0x24,4)))[0],16));record=C.create_string_buffer(b'X'*16,16)
  status=object_region_fn(state,obj,parent,record);assert status>=0
  object_region_pending.append((state.raw,record.raw,status,cpu.reg_read(UC_ARM_REG_R7)))
 if road_full and pc==0x03002320:
  native_state,xyz,branch,branch_record=branch_pending.pop();sp=cpu.reg_read(UC_ARM_REG_SP);actual_xyz=[struct.unpack('<I',bytes(cpu.mem_read(sp+o,4)))[0] for o in (0x10,0xc,8)];assert xyz==actual_xyz and native_state==bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R6),256));branch_checks.append(branch)
  state,record,status,obj=object_region_pending.pop();assert branch==status and (not branch or branch_record==record);assert state==bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R6),256));object_region_checks.append(status)
  if status:
   object_region_predictions.append((obj,record))
  else:assert record==b'X'*16
 if pc==0x030027f0:
  rec=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16));item=dict(region=struct.unpack_from('<H',rec)[0],record=list(struct.unpack('<8H',rec)),caller=cpu.reg_read(UC_ARM_REG_LR),pass_index=cpu.reg_read(UC_ARM_REG_R2),begin=len(draws),end=None,depth=len(active),object=cpu.reg_read(UC_ARM_REG_R7) if cpu.reg_read(UC_ARM_REG_LR)==0x03002364 else 0);
  if road_full and item['caller']==0x03002364:object_region_actual.append((item['object'],rec))
  if road_full and item['caller']==0x03002ae8:
   assert active;static_actual.append((calls.index(active[-1]),rec))
  if road_full and active and item['caller']!=0x03002364:action_actual[calls.index(active[-1])].append((2,0,rec))
  calls.append(item);active.append(item)
  if road_full:
   entry_state=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),256));actions=(NativeAction*515)();action_count=C.c_uint();assert region_actions(entry_state,rec,item['pass_index'],read,None,clip_reciprocal,actions,515,C.byref(action_count));action_expected[len(calls)-1]=[(a.kind,a.mask,bytes(a.record)) for a in actions[:action_count.value]];action_actual[len(calls)-1]=[];
   if not action_snapshots:action_snapshots.append((bytes(cpu.mem_read(0x02000000,0x40000)),bytes(cpu.mem_read(0x03000000,0x10000)),bytes(cpu.mem_read(0x04000000,0x10000))))
   if action_count.value:
    rejected=C.create_string_buffer(b'X'*(515*28),515*28);rejected_count=C.c_uint(123);assert not region_actions(entry_state,rec,item['pass_index'],read,None,clip_reciprocal,rejected,action_count.value-1,C.byref(rejected_count)) and rejected.raw==b'X'*(515*28) and rejected_count.value==123;action_atomic.append(True)
   edge_address=struct.unpack_from('<I',entry_state,104)[0];stream_address=struct.unpack_from('<I',entry_state,108)[0]
   region_entry_inputs.append((entry_state,bytes(cpu.mem_read(edge_address,1664)),bytes(cpu.mem_read(stream_address,1536))))
   gate=collection_gate_fn(entry_state,rec,item['pass_index'],read,None,clip_reciprocal);assert gate>=0
   plan=C.create_string_buffer(4096);amount=C.c_uint();eligible=C.c_uint();assert combined_fn(entry_state,rec,item['pass_index'],read,None,clip_reciprocal,plan,512,C.byref(amount),C.byref(eligible))==1;assert eligible.value==gate
   entry_source_plans[len(calls)-1]=plan.raw[:amount.value*8];combined_checks.append(amount.value)
   if gate:collection_gate_predictions.append(len(calls)-1)
   predicted=C.create_string_buffer(b'X'*16,16);status=static_fn(entry_state,rec,item['pass_index'],read,None,clip_reciprocal,predicted);assert status>=0,(alpha,item['region'],'static eligibility unsupported')
   if status:static_predictions.append((len(calls)-1,predicted.raw))
   else:assert predicted.raw==b'X'*16
 if road_full and pc==0x0300264c:
  mask=cpu.reg_read(UC_ARM_REG_R3);original_command_trace.append((calls.index(active[-1]),4 if mask else 1,mask,bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16))))
  original_phase_trace.append((calls.index(active[-1]),4 if mask else 1,mask,bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16))))
  action_actual[calls.index(active[-1])].append((4 if mask else 1,mask,bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16))))
 if pc==0x03002b68:active.pop()['end']=len(draws)
 if pc==0x03002020:visits.append(dict(index=cpu.reg_read(UC_ARM_REG_R1),region=active[-1]['region'],pass_index=active[-1]['pass_index'],visited=bytes(cpu.mem_read(0x030070c0,32)).hex()))
 if pc==0x03002020:
  index=cpu.reg_read(UC_ARM_REG_R1);base=struct.unpack('<I',cpu.mem_read(cpu.reg_read(UC_ARM_REG_R7)+0x3c,4))[0];obj=bytes(cpu.mem_read(base+index*164,164));bitmap=C.create_string_buffer(bytes(cpu.mem_read(0x030070c0,32)),32);callback=C.c_uint32();result_native=fn(bitmap,32,index,obj,C.byref(callback));pending.append((bitmap.raw,result_native,callback.value))
 if pc in (0x03002090,0x030021f8) and pending:
  bitmap,accepted,callback=pending.pop();assert bytes(cpu.mem_read(0x030070c0,32))==bitmap;assert accepted==int(pc==0x03002090);verified.append(dict(accepted=accepted,callback=callback))
 if road_full and pc==0x03002628:
  ready,expected=owned_model_pending.pop();assert ready==1 and bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),68))==expected;owned_model_checks.append(True);owned_model_extract.update(address=cpu.reg_read(UC_ARM_REG_R0),context=expected)
 if road_full and pc==0x0300262c and owned_model_pending:
  ready,expected=owned_model_pending.pop();assert ready==0
 if pc==0x03002588:
  sp=cpu.reg_read(UC_ARM_REG_SP);params=(C.c_uint32*4)(cpu.reg_read(UC_ARM_REG_R12),*struct.unpack('<2I',cpu.mem_read(sp,8)),struct.unpack('<I',cpu.mem_read(sp+24,4))[0]);context=C.create_string_buffer(bytes(cpu.mem_read(sp+0x48,68)),68)
  status=context_fn(bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R6),256)),bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R7),164)),bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R4),32)),params,read,None,context);assert status>=0;context_pending.append((sp+0x48,context.raw,status))
 if pc in (0x03002628,0x0300262c) and context_pending:
  location,expected,status=context_pending.pop();assert status==int(pc==0x03002628) and bytes(cpu.mem_read(location,68))==expected;contexts.append(dict(ready=status,sha256=hashlib.sha256(expected).hexdigest()))
 if pc==0x030045e0:
  model_reader=read
  if road_full:
   assert owned_model_extract['address']==cpu.reg_read(UC_ARM_REG_R0)
   @Read
   def model_reader(ctx,a,out,n):
    if not read(ctx,a,out,n):return 0
    start=owned_model_extract['address'];lo=max(a,start);hi=min(a+n,start+68)
    if lo<hi:C.memmove(out+lo-a,owned_model_extract['context'][lo-start:hi-start],hi-lo)
    return 1
  model=C.c_void_p();size=C.c_size_t();assert extract(model_reader,None,cpu.reg_read(UC_ARM_REG_R0),struct.unpack_from('<I',result,84)[0],cpu.reg_read(UC_ARM_REG_R7),model_inputs[:48],C.byref(model),C.byref(size))
  try:raw_model=C.string_at(model,size.value)
  finally:d.nf_surface_free(model)
  (p/f'sampled-model-{alpha}{suffix}.bin').write_bytes(raw_model);model_payloads.append(raw_model)
  if road_full:original_command_trace.append((calls.index(active[-1]),5,0,struct.pack('<8H',*active[-1]['record'])))
  if road_full:original_assets.append(raw_model);original_lights.append(None)
  draws.append(dict(kind='model',source=cpu.reg_read(UC_ARM_REG_R7),owner=calls.index(active[-1])));models.append(dict(context_sha256=hashlib.sha256(bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),68))).hexdigest(),region=active[-1]['region'],record=active[-1]['record'],object=cpu.reg_read(UC_ARM_REG_R7)));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 if pc in (0x03000304,0x030032f0):
  if road_full and pc==0x03000304:
   context=cpu.reg_read(UC_ARM_REG_R0);original_wall_leaves.append((cpu.reg_read(UC_ARM_REG_R3),struct.unpack('<I',bytes(cpu.mem_read(context+40,4)))[0],*struct.unpack('<2H',bytes(cpu.mem_read(context+36,4))),bytes(cpu.mem_read(struct.unpack('<I',bytes(cpu.mem_read(context+12,4)))[0],52))))
  if pc==0x030032f0:
   original_affine=struct.unpack('<I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_SP),4)))[0]
   assert active and original_affine==(active[-1]['record'][5]&1),(alpha,'road affine flag region ownership')
   road_state=cpu.reg_read(UC_ARM_REG_R1);state_bytes=bytes(cpu.mem_read(road_state,256))
   if road_full:
    original_road_states.append(state_bytes);context=cpu.reg_read(UC_ARM_REG_R0);sp=cpu.reg_read(UC_ARM_REG_SP);original_road_materials.append((struct.unpack('<I',bytes(cpu.mem_read(context+40,4)))[0],*struct.unpack('<2H',bytes(cpu.mem_read(context+36,4))),cpu.reg_read(UC_ARM_REG_R3),*struct.unpack('<2I',bytes(cpu.mem_read(sp,8)))))
   vertex_base=struct.unpack_from('<I',state_bytes,108)[0];first,amount=struct.unpack_from('<HH',state_bytes,242)
   assert 3<=amount<=64
   vertices=[list(struct.unpack('<6i',bytes(cpu.mem_read(vertex_base+(first+i)*24,24)))) for i in range(amount)]
   if road_clips:
    expected,emitted,original_count=clip_expected;assert emitted==amount and first==original_count
    actual=bytes(cpu.mem_read(vertex_base+first*24,amount*24));assert actual==expected,(alpha,active[-1]['region'],[(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b][:8])
    native_clipped_vertices=expected
    if road_full:
     assert native_region_state==state_bytes,(alpha,active[-1]['region'],'native postclip state')
     state_bytes=native_region_state
    clip_checks.append(dict(region=active[-1]['region'],input_vertices=original_count,output_vertices=amount));clip_expected=None
   road_clip_inputs.append(dict(source=cpu.reg_read(UC_ARM_REG_R7),owner=calls.index(active[-1]),bounds=active[-1]['record'][1:5],state_limits=list(struct.unpack_from('<2H',state_bytes,230)),first=first,vertices=vertices))
   buffer_address=struct.unpack('<I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0)+8,4)))[0]
   current_road=len(road_clip_inputs)-1
   road_clip_inputs[-1]['framebuffer']=list(struct.unpack('<4I',bytes(cpu.mem_read(buffer_address,16))))
   if road_full:
    affine,orientation=struct.unpack('<2I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_SP),8)));context=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),48));shift,height=struct.unpack_from('<2H',context,36)
    offsets=struct.unpack('<2h',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R2)+4,4)));material=[0]*16;material[0]=shift;material[1]=(1<<(shift+15))-1;material[2]=(height<<15)-1;material[5]=struct.unpack_from('<I',context,40)[0];material[14]=(offsets[0]<<7)&0xffffffff;material[15]=(offsets[1]<<7)&0xffffffff
    native_material=C.create_string_buffer(64);descriptor=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R7),48))
    assert seed_fn(state_bytes,descriptor,read,None,native_material) and list(struct.unpack('<16I',native_material.raw))==material
    material=list(struct.unpack('<16I',native_material.raw));seed_checks.append(True)
    native=C.create_string_buffer(40960);n=C.c_uint();bounds=active[-1]['record'][1:5];fb=bytes(cpu.mem_read(buffer_address,16));base=struct.unpack_from('<I',fb)[0]
    args=(native_clipped_vertices,amount,bounds[2],bounds[3],orientation,affine,perspective_reciprocal,fb,struct.pack('<16I',*material))
    assert contexts_fn(*args,native,512,C.byref(n))
    if n.value:
     rejected=C.create_string_buffer(b'X'*40960,40960);rejected_count=C.c_uint(123)
     assert not contexts_fn(*args,rejected,n.value-1,C.byref(rejected_count)) and rejected.raw==b'X'*40960 and rejected_count.value==123;full_atomic.append(True)
    span_contexts=[list(struct.unpack_from('<20I',native.raw,i*80)) for i in range(n.value)];frame=bytearray(cpu.mem_read(base,38400))
    owned_bounds=C.create_string_buffer(8);cell_end=C.c_uint();assert bounds_fn(struct.pack('<4H',*bounds),fb,native,n.value,owned_bounds,C.byref(cell_end))
    road_clip_inputs[-1]['native_clip_bounds']=list(struct.unpack('<4H',owned_bounds.raw));road_clip_inputs[-1]['native_bottom_cell_end']=cell_end.value
    for span in span_contexts:
     params=struct.pack('<16I',*span[4:]);subspans=[span[4:]]
     if span[2]==0x03003190:
      subs=C.create_string_buffer(2048);final=C.create_string_buffer(64);sub_count=C.c_uint();assert perspective_fn(params,perspective_reciprocal,subs,32,C.byref(sub_count),final)
      subspans=[list(struct.unpack_from('<16I',subs.raw,i*64)) for i in range(sub_count.value)]
     for sub in subspans:
      colors=C.create_string_buffer(sub[7]*2);assert pixel_fn(struct.pack('<12I',*sub[:12]),read,None,colors,sub[7])
      for row in range(2 if span[3] else 1):
       offset=sub[6]-base+row*240;assert 0<=offset and offset+len(colors.raw)<=len(frame);frame[offset:offset+len(colors.raw)]=colors.raw
    road_clip_inputs[-1]['affine']=bool(affine)
    road_clip_inputs[-1]['changed_bytes']=sum(a!=b for a,b in zip(frame,bytes(cpu.mem_read(base,38400))))
    full_pending.append((base,frame,span_contexts,0))
   if road_plan:
    affine,orientation=struct.unpack('<2I',bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_SP),8)))
    road_clip_inputs[-1]['plan_flags']=[orientation,affine]
    native=C.create_string_buffer(8192);n=C.c_uint();bounds=active[-1]['record'][1:5]
    assert plan_fn(bytes(cpu.mem_read(vertex_base+first*24,amount*24)),amount,bounds[2],bounds[3],orientation,affine,plan_reciprocal,bytes(cpu.mem_read(buffer_address,16)),native,512,C.byref(n))
    road_clip_inputs[-1]['native_spans']=[list(struct.unpack_from('<4I',native.raw,i*16)) for i in range(n.value)]
  if pc==0x03000304 and active[-1]['object']:
   surface=C.c_void_p();surface_size=C.c_size_t();stage=C.c_uint32();source=cpu.reg_read(UC_ARM_REG_R6)
   extracted=wall(read,None,address,source,model_inputs[48:],1,C.byref(surface),C.byref(surface_size),C.byref(stage))
   raw_surface=None
   if extracted:
    try:raw_surface=C.string_at(surface,surface_size.value)
    finally:d.nf_surface_free(surface)
    (p/f'sampled-object-surface-{alpha}{suffix}.bin').write_bytes(raw_surface)
   object_surfaces.append(dict(source=source,extracted=bool(extracted),stage=stage.value,bytes=surface_size.value,sha256=hashlib.sha256(raw_surface).hexdigest() if raw_surface else None,palette_scope='Exact retained model draw palette; object palette parity not yet proven'))
  if road_full:
   original_asset=C.c_void_p();original_size=C.c_size_t();original_stage=C.c_uint();original_light=C.c_void_p();original_light_size=C.c_size_t()
   if pc==0x03000304:
    owner=C.c_uint32();find_owner=d.nf_wall_owner;find_owner.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p]
    assert find_owner(read,None,address,cpu.reg_read(UC_ARM_REG_R6),C.byref(owner))
    wall_full=d.nf_extract_wall;wall_full.argtypes=[Read,C.c_void_p]+[C.c_uint32]*6+[C.c_void_p]*4
    ready=wall_full(read,None,address,owner.value,cpu.reg_read(UC_ARM_REG_R6),cpu.reg_read(UC_ARM_REG_R0),cpu.reg_read(UC_ARM_REG_R3),cpu.reg_read(UC_ARM_REG_R2),C.byref(original_asset),C.byref(original_size),C.byref(original_light),C.byref(original_light_size))
   else:
    road_extract=d.nf_extract_road_candidate;road_extract.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
    ready=road_extract(read,None,road_state,cpu.reg_read(UC_ARM_REG_R7),model_inputs[48:],1,C.byref(original_asset),C.byref(original_size))
   if ready:
    try:original_assets.append(C.string_at(original_asset,original_size.value))
    finally:d.nf_surface_free(original_asset)
   else:original_assets.append(None)
   original_lights.append(C.string_at(original_light,original_light_size.value) if original_light else None)
   if original_light:d.nf_surface_free(original_light)
  draws.append(dict(kind='wall' if pc==0x03000304 else 'road',source=cpu.reg_read(UC_ARM_REG_R6 if pc==0x03000304 else UC_ARM_REG_R7),owner=calls.index(active[-1])))
  if pc!=0x030032f0 or not road_spans:cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
def pixel_write(cpu,access,location,size,value,ctx):
 if current_road is None:
  key=str(cpu.reg_read(UC_ARM_REG_PC));nonroad_write_pcs[key]=nonroad_write_pcs.get(key,0)+1;return
 assert road_clip_inputs and active
 road_clip_inputs[current_road].setdefault('writes',[]).append([location,size])
 road_clip_inputs[current_road].setdefault('write_pc_counts',{}).setdefault(str(cpu.reg_read(UC_ARM_REG_PC)),0)
 road_clip_inputs[current_road]['write_pc_counts'][str(cpu.reg_read(UC_ARM_REG_PC))]+=1
u.hook_add(UC_HOOK_CODE,hook)
if road_writes:u.hook_add(UC_HOOK_MEM_WRITE,pixel_write,begin=0x06000000,end=0x0601ffff)
for reg,value in ((UC_ARM_REG_R0,address),(UC_ARM_REG_SP,0x0400ff00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,value)
u.emu_start(0x03004d5c,0x03006000,count=5000000)
if road_writes:(p/f'nonroad-write-pcs-{alpha}{suffix}.json').write_text(json.dumps(nonroad_write_pcs,indent=2))
assert u.reg_read(UC_ARM_REG_PC)==0x03006000
if road_full:
 assert source_predictions==source_actual
 assert action_expected==action_actual,(alpha,[(i,action_expected[i],action_actual[i]) for i in action_expected if action_expected[i]!=action_actual[i]])
 Expand=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p)
 Emit=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p)
 class Executor(C.Structure):_fields_=[('expand',Expand),('emit',Emit),('user',C.c_void_p)]+[(key,C.c_uint) for key in ('depth','regions','actions','failed','max_depth','max_regions')]
 execute=d.nf_region_execute;execute.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
 begin=d.nf_region_executor_begin;begin.argtypes=[C.c_void_p,Expand,Emit,C.c_void_p,C.c_uint,C.c_uint]
 execute_queue=d.nf_region_execute_queue;execute_queue.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
 execution_trace=[];execution_entries=[];execution_errors=[];independent_callbacks=[];independent_models=[];independent_source_lists=[];independent_touched_objects=set()
 initial_state=region_entry_inputs[0][0];ew_owned,iw_owned,stack_owned=action_snapshots[0];pool_address=struct.unpack_from('<I',initial_state,60)[0]
 owned_pool=C.create_string_buffer(ew_owned[pool_address-0x02000000:pool_address-0x02000000+256*164],256*164)
 owned_bits=C.create_string_buffer(iw_owned[0x70c0:0x70e0],32)
 @Read
 def immutable_reader(user,a,destination,n):
  for base,data in ((0x02000000,ew_owned),(0x03000000,iw_owned),(0x04000000,stack_owned),(0x08000000,rom)):
   if base<=a and a+n<=base+len(data):
    C.memmove(destination,data[a-base:a-base+n],n)
    lo=max(a,pool_address);hi=min(a+n,pool_address+256*164)
    if lo<hi:C.memmove(destination+lo-a,owned_pool.raw[lo-pool_address:hi-pool_address],hi-lo)
    return 1
  return 0
 matrix_address=struct.unpack_from('<I',initial_state,84)[0];matrix=C.create_string_buffer(48);assert immutable_reader(None,matrix_address,matrix,48)
 @Expand
 def expand_region(ctx,record_ptr,pas,out,capacity,amount):
  try:
   index=len(execution_entries);rec=C.string_at(record_ptr,16);assert rec==struct.pack('<8H',*calls[index]['record']) and pas==calls[index]['pass_index'];execution_entries.append(index)
   return region_actions(initial_state,rec,pas,immutable_reader,None,clip_reciprocal,out,capacity,amount)
  except Exception as error:execution_errors.append(repr(error));return 0
 @Emit
 def emit_region(ctx,executor_ptr,index,action_ptr):
  try:
   action=C.cast(action_ptr,C.POINTER(NativeAction)).contents;rec=bytes(action.record);execution_trace.append((index,action.kind,action.mask,rec))
   if action.kind==3:
    state=C.create_string_buffer(initial_state,256);C.memmove(C.addressof(state)+226,rec[2:10],8)
    sources=C.create_string_buffer(4096);amount=C.c_uint();assert sources_fn(state,rec,immutable_reader,None,sources,512,C.byref(amount));job=NativeDispatch();assert dispatch_begin(C.byref(job),sources,amount.value,256)
    head=C.c_uint(65535);maximum=C.c_uint(0xffffffff);source_region=C.c_uint()
    while dispatch_next(C.byref(job),C.byref(source_region))==1:
     independent_source_lists.append(job.collector.cursor.current)
     selector=C.c_uint()
     while True:
      if job.collector.cursor.current!=65535:independent_touched_objects.add(job.collector.cursor.current)
      status=collector_step(C.byref(job.collector),owned_pool,owned_bits,32,matrix,C.byref(head),C.byref(maximum),C.byref(selector));assert status>=0
      if status==0:break
      if status==2:
       independent_callbacks.append((job.collector.cursor.current,selector.value))
       # All callbacks in this fixture were audited as no-op above.
       assert collector_step(C.byref(job.collector),owned_pool,owned_bits,32,matrix,C.byref(head),C.byref(maximum),C.byref(selector))==1
    assert job.next==job.count
    indices=(C.c_uint32*512)();n=C.c_uint();assert sorted_plan(owned_pool,256,head.value,indices,512,C.byref(n))
    for object_index in indices[:n.value]:
     obj=C.create_string_buffer(owned_pool.raw[object_index*164:(object_index+1)*164],164);xyz=(C.c_uint32*3)();branch=C.c_uint();child=C.create_string_buffer(16)
     assert branch_prepare(state,obj,rec,matrix,xyz,C.byref(branch),child)==1
     if branch.value:
      if not execute(executor_ptr,child,0):return 0
     else:
      material=(C.c_uint32*4)();visible=material_plan(state,obj,xyz,immutable_reader,None,clip_reciprocal,material);assert visible>=0;C.memmove(C.addressof(owned_pool)+object_index*164,obj,164)
      if visible and material[3]==0:
       context=C.create_string_buffer(68);ready=model_plan(state,obj,material,immutable_reader,None,context);assert ready>=0
       if ready:independent_models.append((index,pool_address+object_index*164))
   return 1
  except Exception as error:execution_errors.append(repr(error));return 0
 executor=Executor();assert begin(C.byref(executor),expand_region,emit_region,None,32,4096)
 assert execute_queue(C.byref(executor),result[256:256+count*16],count),execution_errors
 assert owned_bits.raw==bytes(u.mem_read(0x030070c0,32))
 for object_index in independent_touched_objects:
  assert owned_pool.raw[object_index*164:(object_index+1)*164]==bytes(u.mem_read(pool_address+object_index*164,164)),('independent final object',object_index)
 assert independent_callbacks==original_callback_requests and independent_source_lists==source_actual
 assert independent_models==[(v['owner'],v['source']) for v in draws if v['kind']=='model']
 assert execution_entries==list(range(len(calls))) and execution_trace==original_phase_trace and executor.depth==0 and not executor.failed
 class SceneCommand(C.Structure):_fields_=[(key,C.c_uint32) for key in ('kind','owner','pass_index','mask','object','source')]+[('xyz',C.c_uint32*3),('material',C.c_uint32*4),('record',C.c_uint8*16),('state',C.c_uint8*256),('model',C.c_uint8*68),('billboard',C.c_uint32*18),('vertex_count',C.c_uint32),('edge',C.c_uint8*52),('vertices',C.c_int32*(128*6)),('bounds',C.c_uint16*4),('cell_end',C.c_uint32)]
 Callback=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p)
 native_callbacks=[]
 @Callback
 def noop_callback(ctx,index,selector,objects,n,bits,matrix,head,maximum):native_callbacks.append((index,selector));return 1
 producer=d.nf_scene_command_plan;producer.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,Read,C.c_void_p,C.c_void_p,Callback,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
 initial_pool=ew_owned[pool_address-0x02000000:pool_address-0x02000000+256*164];pool=C.create_string_buffer(initial_pool,256*164);bitmap=C.create_string_buffer(iw_owned[0x70c0:0x70e0],32);commands=(SceneCommand*512)();command_count=C.c_uint()
 assert producer(initial_state,result[256:256+count*16],count,pool,256,bitmap,immutable_reader,None,clip_reciprocal,noop_callback,None,commands,512,C.byref(command_count))
 native_command_trace=[(c.owner,{1:'road',2:'wall',5:'model',6:'billboard'}[c.kind],c.source) for c in commands[:command_count.value]]
 assert native_command_trace==[(v['owner'],v['kind'],v['source']) for v in draws] and native_callbacks==original_callback_requests
 roads=[c for c in commands[:command_count.value] if c.kind==1];walls=[c for c in commands[:command_count.value] if c.kind==2]
 for command in roads:
  assert command.xyz[1]==(struct.unpack_from('<H',bytes(command.record),10)[0]&1),(alpha,command.owner,'owned native affine flag')
 (p/f'road-mode-owned-command-{alpha}.json').write_text(json.dumps(dict(result='PASS',road_commands=len(roads),affine=sum(c.xyz[1]!=0 for c in roads),perspective=sum(c.xyz[1]==0 for c in roads),rule='region record u16 +10 bit0; native road command xyz[1]',scope='Original sampled ARM entry flag versus active region record, and native regenerated owned command flag versus its record. Packet/GPU propagation and full-scene pixel fidelity remain incomplete.'),indent=2))
 assert len(roads)==len(road_clip_inputs) and len(walls)==len(original_wall_leaves)
 for command,original,original_state,original_material in zip(roads,road_clip_inputs,original_road_states,original_road_materials):
  assert list(command.material[1:])+list(command.xyz)==list(original_material)
  assert list(command.bounds)==original['native_clip_bounds'] and command.cell_end==original['native_bottom_cell_end']
  assert bytes(command.state)==original_state,(command.owner,'full native command road state')
  assert command.vertex_count==len(original['vertices']) and list(command.vertices[:command.vertex_count*6])==[word for vertex in original['vertices'] for word in vertex],(command.owner,command.vertex_count,len(original['vertices']),[(i,a,b) for i,(a,b) in enumerate(zip(command.vertices[:command.vertex_count*6],[word for vertex in original['vertices'] for word in vertex])) if a!=b][:12])
 for command,original in zip(walls,original_wall_leaves):
  assert list(command.material)==list(original[:4]);assert bytes(command.edge)==original[4]
 assert bitmap.raw==owned_bits.raw
 for object_index in independent_touched_objects:assert pool.raw[object_index*164:(object_index+1)*164]==owned_pool.raw[object_index*164:(object_index+1)*164]
 rejected=C.create_string_buffer(b'X'*(512*C.sizeof(SceneCommand)),512*C.sizeof(SceneCommand));rejected_count=C.c_uint(123);pool=C.create_string_buffer(initial_pool,256*164);bitmap=C.create_string_buffer(iw_owned[0x70c0:0x70e0],32)
 assert not producer(initial_state,result[256:256+count*16],count,pool,256,bitmap,immutable_reader,None,clip_reciprocal,noop_callback,None,rejected,command_count.value-1,C.byref(rejected_count))
 assert rejected.raw==b'X'*(512*C.sizeof(SceneCommand)) and rejected_count.value==123 and pool.raw==initial_pool and bitmap.raw==iw_owned[0x70c0:0x70e0]
 @Read
 def unavailable_reader(ctx,address,out,n):return 0
 for reader_fn,callback_fn in ((immutable_reader,Callback()),(unavailable_reader,noop_callback)):
  pool=C.create_string_buffer(initial_pool,256*164);bitmap=C.create_string_buffer(iw_owned[0x70c0:0x70e0],32)
  assert not producer(initial_state,result[256:256+count*16],count,pool,256,bitmap,reader_fn,None,clip_reciprocal,callback_fn,None,rejected,512,C.byref(rejected_count))
  assert rejected.raw==b'X'*(512*C.sizeof(SceneCommand)) and rejected_count.value==123 and pool.raw==initial_pool and bitmap.raw==iw_owned[0x70c0:0x70e0]
 command_extract=d.nf_extract_scene_command;command_extract.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
 command_assets=[];command_asset_failures=[];command_asset_checks=0
 for i,command in enumerate(commands[:command_count.value]):
  asset=C.c_void_p();asset_size=C.c_size_t();stage=C.c_uint();ok=command_extract(C.byref(command),immutable_reader,None,model_inputs[48:],model_inputs[:48],C.byref(asset),C.byref(asset_size),C.byref(stage))
  if not ok:
   source_bytes=C.create_string_buffer(68);assert immutable_reader(None,command.source,source_bytes,68)
   command_asset_failures.append(dict(ordinal=i,kind=command.kind,source=command.source,stage=stage.value,source_flags=struct.unpack_from('<H',source_bytes.raw,46)[0],command_flags=command.xyz[0],owner=command.owner));continue
  try:
   raw_asset=C.string_at(asset,asset_size.value);assert raw_asset==original_assets[i],(i,command.kind,'owned asset differs from original draw extraction');command_asset_checks+=1
   command_assets.append((command.kind,command.source,raw_asset))
  finally:d.nf_surface_free(asset)
 full_extract=d.nf_extract_scene_command_full;full_extract.argtypes=[C.c_void_p,Read,C.c_void_p]+[C.c_void_p]*7
 full_asset_checks=0;lighting_checks=0;full_failures=[]
 for i,command in enumerate(commands[:command_count.value]):
  asset=C.c_void_p();asset_size=C.c_size_t();light=C.c_void_p();light_size=C.c_size_t();stage=C.c_uint()
  ok=full_extract(C.byref(command),immutable_reader,None,model_inputs[48:],model_inputs[:48],C.byref(asset),C.byref(asset_size),C.byref(light),C.byref(light_size),C.byref(stage))
  if not ok:full_failures.append((i,command.kind,stage.value));continue
  try:
   assert C.string_at(asset,asset_size.value)==original_assets[i],(i,'full owned surface')
   raw_light=C.string_at(light,light_size.value) if light else None
   assert raw_light==original_lights[i],(i,'full owned lighting')
   full_asset_checks+=1;lighting_checks+=bool(raw_light and struct.unpack_from('<I',raw_light)[0])
  finally:d.nf_surface_free(asset);d.nf_surface_free(light)
 assert not full_failures,full_failures
 asset_lighting_atomic=0
 for command in commands[:command_count.value]:
  if command.kind!=2 or command.xyz[0]&256:continue
  rejected_surface=C.c_void_p(123);rejected_surface_size=C.c_size_t(456);rejected_light=C.c_void_p(789);rejected_light_size=C.c_size_t(987);stage=C.c_uint()
  projection=struct.unpack_from('<I',bytes(command.state),80)[0]
  @Read
  def missing_lighting(ctx,a,out,n):
   if a==projection and n==24:return 0
   return immutable_reader(ctx,a,out,n)
  assert not full_extract(C.byref(command),missing_lighting,None,model_inputs[48:],model_inputs[:48],C.byref(rejected_surface),C.byref(rejected_surface_size),C.byref(rejected_light),C.byref(rejected_light_size),C.byref(stage))
  assert (rejected_surface.value,rejected_surface_size.value,rejected_light.value,rejected_light_size.value)==(123,456,789,987)
  asset_lighting_atomic+=1
 (p/f'sampled-native-command-full-assets-{alpha}.json').write_text(json.dumps(dict(result='PASS',commands=command_count.value,original_surface_byte_checks=full_asset_checks,lit_wall_byte_checks=lighting_checks,atomic_lighting_read_rejections=asset_lighting_atomic,scope='Native command world/model/texture assets plus lit wall tables exactly match extraction at original draw contexts; retained single palette and rotation, offline diagnostic.'),indent=2))
 d.nf_draw_palettes_create.argtypes=[C.c_uint64,C.c_uint32];d.nf_draw_palettes_create.restype=C.c_void_p;d.nf_draw_palettes_destroy.argtypes=[C.c_void_p]
 d.nf_draw_palettes_append.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_size_t];d.nf_draw_palettes_seal.argtypes=[C.c_void_p]
 palette_select=d.nf_scene_command_palette;palette_select.argtypes=[C.c_void_p,C.c_uint64,C.c_uint32,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p]
 palette_consensus=d.nf_scene_command_palette_consensus;palette_consensus.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_uint64,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p]
 test_wall=next(c for c in commands[:command_count.value] if c.kind==2)
 harmless=bytearray(model_inputs[48:]);ambiguous=bytearray(model_inputs[48:])
 for offset in range(0,512,2):harmless[offset+1]^=128;ambiguous[offset]^=1
 for conflicting in (False,True):
  bank=d.nf_draw_palettes_create(4,171);assert bank
  try:
   for colors in (model_inputs[48:],bytes(ambiguous if conflicting else harmless)):
    assert d.nf_draw_palettes_append(bank,2,test_wall.source,test_wall.material[0],colors,512)
   assert d.nf_draw_palettes_seal(bank);selected_palette=C.create_string_buffer(b'X'*512,512)
   ready=palette_select(bank,4,171,C.byref(test_wall),immutable_reader,None,model_inputs[:48],selected_palette)
   assert bool(ready)==(not conflicting)
   assert selected_palette.raw==(b'X'*512 if conflicting else model_inputs[48:])
   selected_palette=C.create_string_buffer(b'X'*512,512)
   assert not palette_select(bank,5,171,C.byref(test_wall),immutable_reader,None,model_inputs[:48],selected_palette) and selected_palette.raw==b'X'*512
  finally:d.nf_draw_palettes_destroy(bank)
  banks=[d.nf_draw_palettes_create(4,171),d.nf_draw_palettes_create(4,172)];assert all(banks)
  try:
   for offset,(candidate,colors) in enumerate(zip(banks,(model_inputs[48:],bytes(ambiguous if conflicting else harmless)))):
    assert d.nf_draw_palettes_append(candidate,2,test_wall.source+68*(offset+1),test_wall.material[0],colors,512) and d.nf_draw_palettes_seal(candidate)
   selected_palette=C.create_string_buffer(b'X'*512,512)
   assert not palette_select(banks[0],4,171,C.byref(test_wall),immutable_reader,None,model_inputs[:48],selected_palette) and selected_palette.raw==b'X'*512
   assert bool(palette_consensus(banks[0],171,banks[1],172,4,C.byref(test_wall),immutable_reader,None,model_inputs[:48],selected_palette))==(not conflicting)
   assert selected_palette.raw==(b'X'*512 if conflicting else model_inputs[48:])
   selected_palette=C.create_string_buffer(b'X'*512,512)
   assert not palette_consensus(banks[0],171,banks[1],172,5,C.byref(test_wall),immutable_reader,None,model_inputs[:48],selected_palette) and selected_palette.raw==b'X'*512
  finally:
   for candidate in banks:d.nf_draw_palettes_destroy(candidate)
 (p/f'native-command-palette-{alpha}.json').write_text(json.dumps(dict(result='PASS',visibly_identical_candidates_accepted=True,visible_color_conflict_rejected_atomically=True,wrong_epoch_rejections=4,new_source_pair_palette_consensus=True,consensus_visible_conflict_atomic_rejection=True,scope='Exact kind/source/material candidate resolution with extracted visible texture/lighting color equivalence; no draw-order aliasing.'),indent=2))
 # Independent original-draw asset assembly versus native command-owned extraction.
 d.nf_assembly_create.restype=C.c_void_p;d.nf_assembly_destroy.argtypes=[C.c_void_p];d.nf_scene_packet_free.argtypes=[C.c_void_p]
 d.nf_assembly_surface.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];d.nf_assembly_model.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t]
 d.nf_assembly_bounds.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p];d.nf_assembly_finish.argtypes=[C.c_void_p]+[C.c_uint32]*4+[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p]
 base_packet=(p/'overflow-scene-171/old.bin').read_bytes();packet_header=struct.unpack_from('<8I',base_packet)
 old_sections={t:base_packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',base_packet,32+i*12) for i in range(5))};table=old_sections[4][-131072:]
 ids=[];bounds=[];road_cursor=0;model_cursor=0;reference=d.nf_assembly_create();surface_index=0
 try:
  for i,command in enumerate(commands[:command_count.value]):
   kind=3 if command.kind==5 else command.kind;identity=[kind,address,command.source,command.material[0] if kind==2 else 8 if kind==1 else struct.unpack_from('<I',bytes(command.model),12)[0],0];ids+=identity
   selected=list(struct.unpack_from('<4H',bytes(command.record),2))
   if kind==1:selected=road_clip_inputs[road_cursor]['native_clip_bounds'];road_cursor+=1
   bounds+=selected
   if kind==3:
    # NFB2 carries model clips as well as world clips. Use original ARM region record.
    original_model=models[model_cursor];assert original_model['object']==command.source
    model_clip=original_model['record'][1:5];assert list(command.bounds)==model_clip
    assert d.nf_assembly_model(reference,struct.pack('<5I',*identity),original_assets[i],len(original_assets[i]))
    d.nf_assembly_model_bounds.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
    assert d.nf_assembly_model_bounds(reference,model_cursor,struct.pack('<4H',*model_clip));model_cursor+=1
   else:
    lighting=original_lights[i] or struct.pack('<I',0)
    assert d.nf_assembly_surface(reference,struct.pack('<5I',*identity),original_assets[i],len(original_assets[i]),lighting,len(lighting))
    assert d.nf_assembly_bounds(reference,surface_index,float(alpha),struct.pack('<4H',*selected));surface_index+=1
  ref=C.c_void_p();ref_size=C.c_size_t();assert d.nf_assembly_finish(reference,*packet_header[4:8],table,len(table),C.byref(ref),C.byref(ref_size))
  try:reference_packet=C.string_at(ref,ref_size.value)
  finally:d.nf_scene_packet_free(ref)
 finally:d.nf_assembly_destroy(reference)
 assemble=d.nf_assembly_commands;assemble.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_double,Read,C.c_void_p,C.c_void_p,C.c_void_p]+[C.c_uint32]*4+[C.c_void_p]*3
 owned_ids=(C.c_uint32*len(ids))(*ids);owned_bounds=(C.c_uint16*len(bounds))(*bounds);assembled=C.c_void_p();assembled_size=C.c_size_t()
 assert assemble(commands,command_count.value,owned_ids,None,float(alpha),immutable_reader,None,model_inputs[48:],model_inputs[:48],*packet_header[4:8],table,C.byref(assembled),C.byref(assembled_size))
 try:assembled_packet=C.string_at(assembled,assembled_size.value)
 finally:d.nf_scene_packet_free(assembled)
 assert assembled_packet==reference_packet
 (p/f'overflow-scene-171/native-command-owned-{alpha}.bin').write_bytes(assembled_packet)
 d.nf_visibility_assets_create.argtypes=[C.c_void_p,C.c_size_t];d.nf_visibility_assets_create.restype=C.c_void_p
 d.nf_visibility_assets_release.argtypes=[C.c_void_p];d.nf_visibility_snapshot_create.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_void_p,C.c_void_p];d.nf_visibility_snapshot_create.restype=C.c_void_p
 d.nf_visibility_snapshot_destroy.argtypes=[C.c_void_p];d.nf_visibility_snapshot_bind.argtypes=[C.c_void_p,C.c_void_p];d.nf_visibility_snapshot_set_palette.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t]
 snapshot_packet=d.nf_visibility_snapshot_packet_at;snapshot_packet.argtypes=[C.c_void_p,C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_double,C.c_uint32,C.c_void_p,C.c_uint,C.c_void_p,Callback,C.c_void_p,C.c_void_p,C.c_void_p]
 assets=d.nf_visibility_assets_create(rom,len(rom));assert assets
 selected=struct.unpack_from('<H',iw,0x5d44)[0];snapshot=d.nf_visibility_snapshot_create(assets,ew+iw[:0x8000],0x48000,address,selected,selected,pose[:8],pose[8:56],pose[56:104]);assert snapshot
 d.nf_visibility_assets_release(assets);epoch,serial,begin_refresh,end_refresh=meta['identity']
 identity=C.create_string_buffer(struct.pack('<Q5I',epoch,serial,begin_refresh,end_refresh,begin_refresh,end_refresh),32)
 assert d.nf_visibility_snapshot_set_palette(snapshot,model_inputs[48:],512) and d.nf_visibility_snapshot_bind(snapshot,identity)
 try:
  packet_out=C.c_void_p();packet_size=C.c_size_t()
  assert snapshot_packet(snapshot,epoch,serial,begin_refresh,end_refresh,pose,float(alpha),packet_header[7],initial_pool,256,model_inputs[:48],noop_callback,None,C.byref(packet_out),C.byref(packet_size))
  try:snapshot_raw=C.string_at(packet_out,packet_size.value)
  finally:d.nf_scene_packet_free(packet_out)
  assert snapshot_raw==assembled_packet,'snapshot packet differs from diagnostic native packet'
  native_packet=d.nf_visibility_snapshot_packet_native_at;native_packet.argtypes=snapshot_packet.argtypes[:11]+[C.c_void_p,C.c_void_p]
  native_out=C.c_void_p();native_size=C.c_size_t()
  assert native_packet(snapshot,epoch,serial,begin_refresh,end_refresh,pose,float(alpha),packet_header[7],initial_pool,256,model_inputs[:48],C.byref(native_out),C.byref(native_size))
  try:native_raw=C.string_at(native_out,native_size.value)
  finally:d.nf_scene_packet_free(native_out)
  assert native_raw==assembled_packet,'native callback snapshot packet differs from original scene assets'
  native_detail=(C.c_uint32*6)();d.nf_visibility_snapshot_packet_detail(native_detail);assert native_detail[0]==0
  rejected_native=C.c_void_p(123);rejected_native_size=C.c_size_t(456)
  assert not native_packet(snapshot,epoch+1,serial,begin_refresh,end_refresh,pose,float(alpha),packet_header[7],initial_pool,256,model_inputs[:48],C.byref(rejected_native),C.byref(rejected_native_size)) and (rejected_native.value,rejected_native_size.value)==(123,456)
  unsupported_pool=bytearray(initial_pool)
  for object_index in range(256):
   if struct.unpack_from('<H',unsupported_pool,object_index*164+78)[0]==12:struct.pack_into('<H',unsupported_pool,object_index*164+78,13)
  assert not native_packet(snapshot,epoch,serial,begin_refresh,end_refresh,pose,float(alpha),packet_header[7],bytes(unsupported_pool),256,model_inputs[:48],C.byref(rejected_native),C.byref(rejected_native_size)) and (rejected_native.value,rejected_native_size.value)==(123,456)
  assert native_packet(snapshot,epoch,serial,begin_refresh,end_refresh,pose,float(alpha),packet_header[7],initial_pool,256,model_inputs[:48],C.byref(native_out),C.byref(native_size))
  try:assert C.string_at(native_out,native_size.value)==native_raw
  finally:d.nf_scene_packet_free(native_out)
  (p/f'native-callback-snapshot-packet-{alpha}.json').write_text(json.dumps(dict(result='PASS',packet_bytes=len(native_raw),native_callback_calls=native_detail[5],original_scene_asset_packet_exact=True,scope='Native snapshot planner executes owned selector12 state/ground/damage/projection callbacks; exact complete packet versus independently extracted original sampled scene. Fixture callback changes remain limited; sound delivery suppressed for rendering.'),indent=2))
  rejected_snapshot_out=C.c_void_p(123);rejected_snapshot_size=C.c_size_t(456)
  for bad_epoch,bad_serial,bad_begin,bad_end in ((epoch+1,serial,begin_refresh,end_refresh),(epoch,serial+1,begin_refresh,end_refresh),(epoch,serial,begin_refresh+1,end_refresh),(epoch,serial,begin_refresh,end_refresh+1)):
   assert not snapshot_packet(snapshot,bad_epoch,bad_serial,bad_begin,bad_end,pose,float(alpha),packet_header[7],initial_pool,256,model_inputs[:48],noop_callback,None,C.byref(rejected_snapshot_out),C.byref(rejected_snapshot_size))
   assert (rejected_snapshot_out.value,rejected_snapshot_size.value)==(123,456)
  @Callback
  def changing_camera(ctx,index,selector,objects,n,bits,matrix,head,maximum):
   words=C.cast(matrix,C.POINTER(C.c_uint32));words[0]^=1;return 1
  for callback_fn in (Callback(),changing_camera):
   assert not snapshot_packet(snapshot,epoch,serial,begin_refresh,end_refresh,pose,float(alpha),packet_header[7],initial_pool,256,model_inputs[:48],callback_fn,None,C.byref(rejected_snapshot_out),C.byref(rejected_snapshot_size))
   assert (rejected_snapshot_out.value,rejected_snapshot_size.value)==(123,456)
  repeat_out=C.c_void_p();repeat_size=C.c_size_t()
  assert snapshot_packet(snapshot,epoch,serial,begin_refresh,end_refresh,pose,float(alpha),packet_header[7],initial_pool,256,model_inputs[:48],noop_callback,None,C.byref(repeat_out),C.byref(repeat_size))
  try:assert C.string_at(repeat_out,repeat_size.value)==snapshot_raw
  finally:d.nf_scene_packet_free(repeat_out)
  (p/f'native-snapshot-packet-{alpha}.json').write_text(json.dumps(dict(result='PASS',packet_bytes=len(snapshot_raw),native_diagnostic_packet_byte_parity=True,identity_atomic_rejections=4,callback_atomic_rejections=2,repeat_after_rejections_exact=True,scope='Identity-bound owned snapshot re-evaluates visibility and generates native commands/assets/bounds/packet. Caller supplies coherent sampled object pool, rotation and audited callback adapter.'),indent=2))
 finally:d.nf_visibility_snapshot_destroy(snapshot)
 rejected_packet=C.c_void_p(123);rejected_packet_size=C.c_size_t(456)
 assert not assemble(commands,command_count.value,owned_ids,None,float(alpha),unavailable_reader,None,model_inputs[48:],model_inputs[:48],*packet_header[4:8],table,C.byref(rejected_packet),C.byref(rejected_packet_size))
 assert (rejected_packet.value,rejected_packet_size.value)==(123,456)
 last_kind=commands[command_count.value-1].kind;commands[command_count.value-1].kind=6
 assert not assemble(commands,command_count.value,owned_ids,None,float(alpha),immutable_reader,None,model_inputs[48:],model_inputs[:48],*packet_header[4:8],table,C.byref(rejected_packet),C.byref(rejected_packet_size))
 assert (rejected_packet.value,rejected_packet_size.value)==(123,456)
 commands[command_count.value-1].kind=last_kind
 bounded_index=next(i for i in reversed(range(command_count.value)) if commands[i].kind in (1,2));original_bottom=commands[bounded_index].bounds[3];commands[bounded_index].bounds[3]=161
 assert not assemble(commands,command_count.value,owned_ids,None,float(alpha),immutable_reader,None,model_inputs[48:],model_inputs[:48],*packet_header[4:8],table,C.byref(rejected_packet),C.byref(rejected_packet_size))
 assert (rejected_packet.value,rejected_packet_size.value)==(123,456);commands[bounded_index].bounds[3]=original_bottom
 original_identity_source=owned_ids[2];owned_ids[2]+=1
 assert not assemble(commands,command_count.value,owned_ids,None,float(alpha),immutable_reader,None,model_inputs[48:],model_inputs[:48],*packet_header[4:8],table,C.byref(rejected_packet),C.byref(rejected_packet_size))
 assert (rejected_packet.value,rejected_packet_size.value)==(123,456);owned_ids[2]=original_identity_source
 (p/f'native-command-assembly-{alpha}.json').write_text(json.dumps(dict(result='PASS',commands=command_count.value,bytes=len(assembled_packet),original_asset_packet_byte_parity=True,owned_command_bounds=True,atomic_rejections=4,scope='C asset extraction and bounded packet assembly from native commands; identities and native component bounds supplied by diagnostic owner. Offline, no live timing verification.'),indent=2))
 rejected_asset=C.c_void_p(123);rejected_size=C.c_size_t(456);rejected_stage=C.c_uint()
 assert not command_extract(C.byref(commands[0]),unavailable_reader,None,model_inputs[48:],model_inputs[:48],C.byref(rejected_asset),C.byref(rejected_size),C.byref(rejected_stage))
 assert rejected_asset.value==123 and rejected_size.value==456
 unsupported=SceneCommand();unsupported.kind=6
 assert not command_extract(C.byref(unsupported),immutable_reader,None,model_inputs[48:],model_inputs[:48],C.byref(rejected_asset),C.byref(rejected_size),C.byref(rejected_stage))
 assert rejected_asset.value==123 and rejected_size.value==456
 (p/f'sampled-native-command-assets-{alpha}.json').write_text(json.dumps(dict(result='PASS' if not command_asset_failures else 'INCOMPLETE',owned_assets=len(command_assets),original_draw_byte_checks=command_asset_checks,atomic_read_and_unsupported_rejections=2,commands=command_count.value,failures=command_asset_failures,scope='Owned world/model extraction directly from native commands and one scene snapshot; primary roads/default unlit walls/model only. Palette supplied from retained draw.'),indent=2))
 (p/f'sampled-native-command-plan-{alpha}.json').write_text(json.dumps(dict(result='PASS',native_commands=command_count.value,model_leaves=sum(c.kind==5 for c in commands[:command_count.value]),wall_leaves=len(walls),road_leaves=len(roads),road_clipped_vertices=sum(c.vertex_count for c in roads),full_road_state_checks=len(roads),owned_road_bounds_checks=len(roads),full_wall_scratch_checks=len(walls),atomic_capacity_rejection=True,atomic_missing_callback_and_read_rejections=2,scope='Entire C traversal/source/collector/branch/material/model producer from one snapshot. Commands match all original wall/road/model occurrence order and final traversed object state; audited fixture callback adapter is no-op.'),indent=2))
 (p/f'sampled-native-executor-{alpha}.json').write_text(json.dumps(dict(result='PASS',native_region_entries=executor.regions,native_phase_actions=executor.actions,emitted_phases=len(execution_trace),independent_sources=len(independent_source_lists),independent_callbacks=len(independent_callbacks),independent_models=len(independent_models),final_traversed_object_records=len(independent_touched_objects),final_visit_bytes=32,scope='Native depth-first root/static/object-child traversal and phase ordering versus original. One initial owned snapshot/state/pool/bitmap; native source/collector/sorted/branch/material/model composition derives object children independently. Fixture callbacks audited as no-op. Surface command emission and broader callback semantics remain external.'),indent=2))

 (p/f'sampled-region-actions-{alpha}.json').write_text(json.dumps(dict(result='PASS',region_invocations=len(action_expected),native_actions=sum(map(len,action_expected.values())),atomic_capacity_rejections=len(action_atomic),scope='Native ordered region phases, child records and deferred masks match original local execution; recursive action consumption still original.'),indent=2))
 assert not owned_model_pending
 (p/f'sampled-object-model-plan-{alpha}.json').write_text(json.dumps(dict(result='PASS',native_model_contexts=len(owned_model_checks),scope='Model context composed before original model branch from native material plan; full68byte context matches original renderer input. Scratch seed bytes retained.'),indent=2))
 assert not material_pending
 (p/f'sampled-object-material-{alpha}.json').write_text(json.dumps(dict(result='PASS',material_decisions=len(material_checks),billboard_branches=material_checks.count(1),model_branches=material_checks.count(0),culled=material_checks.count(-1),scope='Composed native cull/material/texture branch matches original registers and object bytes; downstream draw execution retained.'),indent=2))
 assert not branch_pending
 (p/f'sampled-object-branch-{alpha}.json').write_text(json.dumps(dict(result='PASS',prepared_sorted_objects=len(branch_checks),recursive_region_branches=sum(branch_checks),scope='Composed native setup from owned sorted objects matches full state, XYZ and recursive record at original2320; downstream material/draw execution still original.'),indent=2))
 (p/f'sampled-sorted-plan-{alpha}.json').write_text(json.dumps(dict(result='PASS',completed_collection_plans=len(sorted_plan_checks),planned_object_draws=sum(sorted_plan_checks),scope='Native ordered draw indices from owned collection snapshots match original sorted object dispatch; recursive scheduling/draw execution still original.'),indent=2))
 for job in dispatch_jobs.values():
  sentinel=C.c_uint(123);assert dispatch_next(C.byref(job),C.byref(sentinel))==0 and sentinel.value==123
 (p/f'sampled-object-dispatch-{alpha}.json').write_text(json.dumps(dict(result='PASS',region_plans=len(dispatch_jobs),native_source_starts=len(dispatch_checks),scope='Owned native source-plan dispatcher supplies collector roots and verifies exhaustion; original call scheduling/callback effects/draw execution retained.'),indent=2))
 (p/f'sampled-region-object-plan-{alpha}.json').write_text(json.dumps(dict(result='PASS',region_entries=len(combined_checks),source_lists=sum(combined_checks),scope='Composed native eligibility and ordered source plans from pre-dispatch inputs match every original collection invocation; callbacks and recursive execution still original.'),indent=2))
 assert sorted(collection_gate_predictions)==sorted(collection_gate_actual)
 (p/f'sampled-object-gate-{alpha}.json').write_text(json.dumps(dict(result='PASS',region_entries=len(region_entry_inputs),native_collections=len(collection_gate_predictions),scope='Native enclosing pass/material/geometry/record/callback-table gates match actual54A0 invocation membership; nested dispatch timing still original.'),indent=2))
 (p/f'sampled-object-sources-{alpha}.json').write_text(json.dumps(dict(result='PASS',eligible_region_invocations=len(source_checks),native_source_lists=len(source_predictions),scope='Native54A0 ordered source-head plans match every actual2000 traversal. Eligibility for enclosing54A0 invocation still original.'),indent=2))
 assert not collector_context and (not native_sorted_draw or native_sorted_draw['next']==65535)
 (p/f'sampled-owned-collector-{alpha}.json').write_text(json.dumps(dict(result='PASS',complete_lists=len(collector_checks),native_sorted_draw_checks=len(native_draw_checks),source_steps=sum(collector_checks),callback_handoffs=len(collector_callbacks),callback_changed_bytes=sum(collector_callbacks),scope='One owned native pool/bitmap/sorted state per complete sampled source list; callback deltas observed from original execution and applied explicitly. No game callback port or live native gameplay claim.'),indent=2))
 assert not sort_pending
 (p/f'sampled-object-sort-{alpha}.json').write_text(json.dumps(dict(result='PASS',post_visit_sort_calls=len(sort_checks),inserted=sum(sort_checks),scope='Native post-callback sorting consumes sampled pool/matrix and matches complete pool plus sorted head/maximum. Original callback effects and source traversal retained.'),indent=2))
 assert not object_region_pending and object_region_predictions==object_region_actual
 (p/f'sampled-object-region-{alpha}.json').write_text(json.dumps(dict(result='PASS',object_preparations=len(object_region_checks),native_region_calls=sum(object_region_checks),scope='Native viewport/state and object flag region records match original sampled dispatch. Object selection/sort/callback eligibility still original.'),indent=2))
 assert static_predictions==static_actual,(alpha,static_predictions,static_actual)
 (p/f'sampled-static-eligibility-{alpha}.json').write_text(json.dumps(dict(result='PASS',region_entries=len(region_entry_inputs),native_static_children=len(static_predictions),scope='Every sampled original region entry evaluated for native static-child eligibility. Native predicted records/parent occurrences equal actual recursive calls; root membership/object callbacks still original.'),indent=2))
assert not context_pending and len(contexts)==1 and contexts[0]["ready"]==1
assert not active and not pending and len(verified)==len(visits)
assert len(models)==1 and models[0]['region']==87
repeat=[i for i,v in enumerate(visits) if v['region']==87];assert all(visits[i]['index']==0 for i in repeat)
assert verified[repeat[0]]['accepted']==1 and all(verified[i]['accepted']==0 for i in repeat[1:])
first87=next(v for v in calls if v['region']==87 and v['pass_index']==1);assert models[0]['record']==first87['record']
assert len([v for v in calls if v['caller']==0x03002364 and v['region']==90])==1
raw_model=model_payloads[0]
if road_full:
 assert not full_pending
 (p/f'road-full-parity-{alpha}.json').write_text(json.dumps(dict(result='PASS',roads=len(full_checks),affine_roads=sum(c['affine'] for c in full_checks),perspective_roads=sum(not c['affine'] for c in full_checks),near_clipped_roads=sum(c['near_clipped_edges']>0 for c in full_checks),near_clipped_edges=sum(c['near_clipped_edges'] for c in full_checks),near_clipped_roads_changing_framebuffer=sum(c['near_clipped_edges']>0 and c['changed_bytes']>0 for c in full_checks),affine_roads_changing_framebuffer=sum(c['affine'] and c['changed_bytes']>0 for c in full_checks),perspective_roads_changing_framebuffer=sum(not c['affine'] and c['changed_bytes']>0 for c in full_checks),roads_changing_framebuffer=sum(c['changed_bytes']>0 for c in full_checks),changed_framebuffer_bytes=sum(c['changed_bytes'] for c in full_checks),road_checks=full_checks,spans=sum(c['spans'] for c in full_checks),native_geometry_calls=len(geometry_checks),native_region_state_checks=2*len(geometry_checks),native_material_calls=len(seed_checks),native_preclip_vertices=sum(c['vertices'] for c in geometry_checks),atomic_capacity_rejections=len(full_atomic),scope='Native region reconstruction, horizontal clipping, span contexts, subdivision and colors compose full road scratch framebuffer byte-for-byte. Eligibility/call records still supplied by original dispatcher. Native region setup/transform/geometry begins from owned pre-dispatch inputs; complete256byte preclip/postclip state parity verified; material/animation resolution native. Offline source-resolution component, not native4K/live gameplay.'),indent=2))
if road_writes:
 assert not pixel_pending
 assert not perspective_pending
 (p/f'road-perspective-parity-{alpha}.json').write_text(json.dumps(dict(result='PASS',calls=len(perspective_checks),subspans=sum(perspective_checks),scope='Native perspective16sample subdivision contexts and final mutated context match original03003190; colors independently checked at writer return.'),indent=2))
 (p/f'road-color-parity-{alpha}.json').write_text(json.dumps(dict(result='PASS',spans=len(pixel_checks),samples=sum(c['samples'] for c in pixel_checks),doubled_spans=sum(c['doubled'] for c in pixel_checks),scope='Native030056d8 sampled colors match original scratch VRAM in both written rows; perspective03190 inline sampling not covered.'),indent=2))
if road_plan:
 for c in road_clip_inputs:
  expected=[[s['params'][6],s['params'][7],s['routine'],s['doubled']] for s in c.get('spans',[])]
  assert expected==c['native_spans'],(alpha,c['source'],expected[:5],c['native_spans'][:5],len(expected),len(c['native_spans']))
 (p/f'road-plan-parity-{alpha}.json').write_text(json.dumps(dict(result='PASS',roads=len(road_clip_inputs),spans=sum(len(c['native_spans']) for c in road_clip_inputs),scope='Native coverage span schedule matches original destination,width,routine and doubled-row flag; texture interpolation not compared.'),indent=2))
if road_edges:
 assert not edge_pending
 (p/f'road-edge-parity-{alpha}.json').write_text(json.dumps(dict(result='PASS',calls=len(edge_checks),accepted=sum(edge_checks),rejected=len(edge_checks)-sum(edge_checks),scope='Native edge context matches original03002f88 on captured sampled scene; span writers stubbed.'),indent=2))
if road_clips:(p/f'road-polygon-parity-{alpha}.json').write_text(json.dumps(dict(result='PASS',cases=clip_checks,scope='Native projected attribute clipping compared byte-for-byte against original03000efc at road entry; offline component only.'),indent=2))
(p/f'road-clip-inputs-{alpha}{suffix}.json').write_text(json.dumps(dict(alpha=float(alpha),cases=road_clip_inputs,scope='Original region clipping output at road entry; raster stubbed, coverage not yet verified.'),indent=2))
report=dict(object_surfaces=object_surfaces,object_motion=motion,sampled_object_q8_xyz=sampled_object_pose,regenerated_model_bytes=len(raw_model),regenerated_model_sha256=hashlib.sha256(raw_model).hexdigest(),model_scope='Sampled camera/context and interpolated object pose' if motion else 'Sampled camera/context with retained earlier object pose',native_context_checks=contexts,alpha=float(alpha),queue_count=count,draws=draws,native_visit_checks=verified,result='PASS',calls=calls,models=models,visits=visits,scope='Original sampled root dispatcher and object eligibility; wall, road and model raster routines stubbed. Offline diagnostic, not gameplay.')
if road_spans:report['scope']='Original sampled dispatcher and road edge setup execute; wall/model raster stubbed. Road texture writers '+('execute in private scratch VRAM.' if road_writes else 'stubbed.')+' Offline diagnostic, not gameplay.'
(p/f'sampled-object-dispatch-{alpha}{suffix}-tests.json').write_text(json.dumps(report,indent=2));print(dict(result=report['result'],alpha=alpha,draws=len(draws),calls=len(calls),models=len(models),native_visits=len(verified)))







