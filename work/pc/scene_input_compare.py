"""Test-only views of all prepared inputs used by the native scene renderer."""
import ctypes as C
from source_frame_witness import function as fn,P,S,U,Q

def prepared_inputs(d,scene):
 m=(Q*8)();assert fn(d,'nf_pc_scene_info',[P,P])(scene,m);parts={}
 def view(name,args):
  pointer=P();size=S();ok=fn(d,name,[P]+[U]*(len(args)-1)+[P,P])(*args,C.byref(pointer),C.byref(size))
  return C.string_at(pointer,size.value) if ok else None
 for k in range(2):parts[f'base{k}']=view('nf_pc_scene_buffer',[scene,k])
 for k in range(3):parts[f'hud{k}']=view('nf_pc_scene_hud_buffer',[scene,k])
 for owner in range(int(m[2])):
  for kind in [2,3]:
   for k in range(3):parts[f'retention{owner}/{kind}/{k}']=view('nf_pc_scene_retention_buffer',[scene,owner,kind,k])
 for command in range(int(m[3])):
  cm=(Q*16)();assert fn(d,'nf_pc_scene_command_info',[P,U,P])(scene,command,cm);parts[f'command{command}/info']=bytes(cm)
  for k in range(2):parts[f'command{command}/buffer{k}']=view('nf_pc_scene_command_buffer',[scene,command,k])
  for level in range(32 if cm[8] else 1):parts[f'command{command}/image{level}']=view('nf_pc_scene_command_image',[scene,command,level])
  columns=(U*3240)();ok=fn(d,'nf_pc_scene_command_columns',[P,U,U,P,S])(scene,command,3240,columns,C.sizeof(columns));parts[f'command{command}/columns']=bytes(columns) if ok else None
 return list(m),parts
