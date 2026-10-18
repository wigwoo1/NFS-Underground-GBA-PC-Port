# Reuses the verified background transfer adversarial suite for both owned source kinds.
from pathlib import Path
import subprocess,sys
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-owned-sources-tests')
s=(here/'test_owned_background_candidate.py').read_text(encoding='utf-8-sig')
s=s.replace('NFSUG-pc-owned-background-tests','NFSUG-pc-owned-sources-tests').replace('owned-background-build-report.json','owned-sources-build-report.json')
s=s.replace('PASS_OWNED_BACKGROUND_FRAME_LIFETIMES','PASS_OWNED_SOURCES_FRAME_LIFETIMES').replace('PASS_OWNED_BACKGROUND_CORE_PARITY','PASS_OWNED_SOURCES_CORE_PARITY')
s=s.replace('background_copy_bytes_removed_first_captures','owned_source_copy_bytes_removed_first_captures')
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace('here=Path(__file__).resolve().parent;',f'here=Path({str(here)!r});')
replace("Release=C.CFUNCTYPE(None,P)","Release=C.CFUNCTYPE(None,P)\nTakeOwner=C.CFUNCTYPE(S,P,Q,U,U,U,C.POINTER(P))")
replace("op=fn('nf_pc_source_reader_open_owned_background',[P,S,P,P],P)","op=fn('nf_pc_source_reader_open_owned_sources',[P,S,P,P,P,P],P)")
replace("fault={'name':None,'take':'valid'}","fault={'name':None,'take':'valid','geometry_take':'valid'}")
replace(' @Release\n def release(pointer):',''' @TakeOwner
 def take_geometry(core,e,serial,begin,end,pointer):
  global allocated
  pointer[0]=None;raw=data.get(('geometry',(e,serial,begin,end)))
  if raw is None or fault['name']=='geometry':return 0
  mode=fault['geometry_take']
  if mode=='null':return len(raw)
  raw=bytes(raw)
  if mode=='corrupt':raw=bytes(8)+raw[8:]
  if mode=='oversize':raw=b'x'
  buffer=C.create_string_buffer(raw,len(raw));address=C.addressof(buffer);allocations[address]=buffer;pointer[0]=address;allocated+=1
  return 0 if mode=='zero' else 64*1024*1024+1 if mode=='oversize' else len(raw)
 @Release
 def release(pointer):''')
replace('reader=op(C.byref(api),64*1024*1024,addr(take),addr(release));','reader=op(C.byref(api),64*1024*1024,addr(take),addr(release),addr(take_geometry),addr(release));')
replace("assert frame and 'background' not in calls","assert frame and 'background' not in calls and 'geometry' not in calls")
replace("assert oldstats[4]-newstats[4]==len(original);bytes_saved+=len(original)","removed=len(original)+sum(len(raw) for (i,k),raw in expected.items() if k==1);assert oldstats[4]-newstats[4]==removed;bytes_saved+=removed")
replace("fault['take']='valid'\n for name", "fault['take']='valid'\n for mode in ['zero','null','oversize','corrupt']:\n  fault['geometry_take']=mode;assert not cap(reader,64*1024*1024),(path.name,'geometry',mode)\n fault['geometry_take']='valid'\n for name")
replace('op(C.byref(api),64*1024*1024,None,addr(release))','op(C.byref(api),64*1024*1024,None,addr(release),addr(take_geometry),addr(release))')
replace('op(C.byref(api),64*1024*1024,addr(take),None)','op(C.byref(api),64*1024*1024,addr(take),None,addr(take_geometry),addr(release))')
replace("rop_owned=fn(adapter,'nf_pc_source_reader_open_owned_background',[P,S,P,P],P)","rop_owned=fn(adapter,'nf_pc_source_reader_open_owned_sources',[P,S,P,P,P,P],P)")
replace('C.cast(dll.nfa_core_capture_owned_free,P)) if dll is new', 'C.cast(dll.nfa_core_capture_owned_free,P),C.cast(dll.nfa_core_capture_source_world_take,P),C.cast(dll.nfa_core_capture_source_world_free,P)) if dll is new')
replace("base/'NFSUG-pc-owned-assembly-core-tests/capture-host.dll'","base/'NFSUG-pc-owned-background-tests/capture-host.dll'")
replace(r'life[0]>0\n',r"life[0]>0\ngeometry_life=(Q*3)();assert fn(new,'nfa_core_capture_owned_geometry_info',[P])(geometry_life) and geometry_life[0]==geometry_life[1] and geometry_life[0]>0\n")
replace('background_releases=int(life[1]),','background_releases=int(life[1]),geometry_allocations=int(geometry_life[0]),geometry_releases=int(geometry_life[1]),')
p=out/'test-owned-sources-expanded.py';p.write_text(s);subprocess.run([sys.executable,str(p)],check=True)
