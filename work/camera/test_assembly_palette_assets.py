"""Assembly reuses validated world assets and preserves complete packet bytes."""
from pathlib import Path
import ctypes as C,json,runpy,sys
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['oracle','0.5']
fixture=runpy.run_path(str(p/'test_classified_command_scene.py'));ns=fixture['ns'];d=ns['d'];P=C.c_void_p;U=C.c_uint;Z=C.c_size_t;Read=ns['Read']
Palette=fixture['Palette'];Inputs=fixture['Inputs']
Assets=C.CFUNCTYPE(C.c_int,P,U,P,Read,P,P,P,C.POINTER(P),C.POINTER(Z),C.POINTER(P),C.POINTER(Z))
d.nf_draw_palettes_create.argtypes=[C.c_uint64,U];d.nf_draw_palettes_create.restype=P
d.nf_draw_palettes_append.argtypes=[P,U,U,U,P,Z];d.nf_draw_palettes_seal.argtypes=[P];d.nf_draw_palettes_destroy.argtypes=[P]
select=d.nf_scene_command_palette;select.argtypes=[P,C.c_uint64,U,P,Read,P,P,P]
extract=d.nf_scene_command_palette_extract;extract.argtypes=[P,C.c_uint64,U,P,Read,P,P,P,C.POINTER(P),C.POINTER(Z),C.POINTER(P),C.POINTER(Z)]
banks={};calls=[];palette=ns['model_inputs'][48:]
for i,c in enumerate(ns['commands'][:ns['command_count'].value]):
 if c.kind not in (1,2):continue
 bank=d.nf_draw_palettes_create(43,17);assert bank
 assert d.nf_draw_palettes_append(bank,c.kind,c.source,c.material[1 if c.kind==1 else 0],palette,512) and d.nf_draw_palettes_seal(bank);banks[i]=bank
@Palette
def old(ctx,i,c,read,user,rotation,out):return select(banks[i],43,17,c,read,user,rotation,out)
@Assets
def reused(ctx,i,c,read,user,rotation,out,a,az,l,lz):return extract(banks[i],43,17,c,read,user,rotation,out,a,az,l,lz)
@Read
def reader(ctx,address,out,size):calls.append((address,size));return ns['immutable_reader'](ctx,address,out,size)
def build(name,callback,callback_type):
 fn=getattr(d,name);fn.argtypes=[P,U,P,P,C.c_double,Read,P,callback_type,P,P,Inputs,P,U,U,U,U,P,C.POINTER(P),C.POINTER(Z)]
 out=P(123);size=Z(456)
 result=fn(ns['commands'],ns['command_count'].value,ns['owned_ids'],None,.5,reader,None,callback,None,ns['model_inputs'][:48],fixture['inputs'],None,*ns['packet_header'][4:8],ns['table'],C.byref(out),C.byref(size))
 if not result:assert (out.value,size.value)==(123,456);return None
 try:return C.string_at(out,size.value)
 finally:d.nf_scene_packet_free(out)
try:
 original=build('nf_assembly_commands_classified_world_model_inputs',old,Palette);before=len(calls);calls.clear()
 result=build('nf_assembly_commands_classified_assets_model_inputs',reused,Assets);after=len(calls)
 assert result==original==fixture['packet'] and after<before
 @Assets
 def failing(ctx,i,c,read,user,rotation,out,a,az,l,lz):
  return 0 if i==max(banks) else reused(ctx,i,c,read,user,rotation,out,a,az,l,lz)
 assert build('nf_assembly_commands_classified_assets_model_inputs',failing,Assets) is None
 assert build('nf_assembly_commands_classified_assets_model_inputs',reused,Assets)==result
finally:
 for bank in banks.values():d.nf_draw_palettes_destroy(bank)
report=dict(result='PASS',commands=ns['command_count'].value,packet_bytes=len(result),exact_packet_parity=True,scene_reads_previous=before,scene_reads_reused=after,late_resolver_rejection_atomic=True,repeat_after_rejection_exact=True,scope='Complete captured midpoint command assembly with owned validated assets; snapshot/live provider still pending.')
(p/'assembly-palette-assets-tests.json').write_text(json.dumps(report,indent=2));print(report)
