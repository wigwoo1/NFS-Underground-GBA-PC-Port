"""Inspect actual Android ELF machine, page alignment and defined API exports."""
import argparse,hashlib,json,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--report",type=Path,required=True)
p.add_argument("--jni",action="store_true")
a=p.parse_args()
required={"nfa_core_open","nfa_core_close","nfa_core_step","nfa_core_pause","nfa_core_timing","nfa_core_pixels","nfa_core_state_size","nfa_core_load_state","nfa_core_save_state","nfa_core_read_audio","nfa_touch_clear","nfa_touch_set","nfa_touch_keys","nfa_core_battery_size","nfa_core_copy_battery","nfa_core_load_battery"}
if a.jni:
 required.update("Java_org_codex_nfsugpreview_NativeCore_"+name for name in
  ("openNative","closeNative","stepNative","pauseNative","timingNative","frameNative","audioNative","snapshotNative","restoreNative","captureSupportedNative","captureEnableNative","captureStatsNative","capturePacketNative","captureLayersNative","captureSceneNative"))
targets=[]
for abi,machine in (("arm64-v8a",183),("x86_64",62)):
 file=a.root/("build-"+abi)/"libnfsug_android_core.so";data=file.read_bytes()
 assert data[:6]==b"\x7fELF\x02\x01"
 assert struct.unpack_from("<HH",data,16)==(3,machine)
 phoff,shoff=struct.unpack_from("<QQ",data,32);phsize,phnum,shsize,shnum=struct.unpack_from("<4H",data,54)
 loads=[]
 for i in range(phnum):
  ph=struct.unpack_from("<II6Q",data,phoff+i*phsize)
  if ph[0]==1:loads.append(ph[-1])
 assert loads and all(n>=16384 for n in loads)
 sections=[struct.unpack_from("<II4QII2Q",data,shoff+i*shsize) for i in range(shnum)]
 exports=set();undefined=set()
 for section in sections:
  if section[1]!=11:continue
  offset,size,link,stride=section[4],section[5],section[6],section[9]
  strings=sections[link];names=data[strings[4]:strings[4]+strings[5]]
  for at in range(offset,offset+size,stride):
   name,info,other,index,value,symbolsize=struct.unpack_from("<IBBHQQ",data,at)
   end=names.find(b"\0",name);text=names[name:end].decode("utf-8")
   if not index:undefined.add(text)
   elif info&15==2 and info>>4 in (1,2) and other&3 in (0,3):exports.add(text)
 assert required<=exports,required-exports
 commands=json.loads((a.root/("build-"+abi)/"compile_commands.json").read_text())
 command=next(row["command"] for row in commands if row["file"].replace("\\","/").endswith("/nfsug_android_core.c"))
 assert "android26" in command and "windows-gnu" not in command
 targets.append(dict(abi=abi,machine=machine,elf_class=64,load_page_alignments=loads,api_exports=sorted(required),
   bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),undefined_imports=sorted(undefined-{""," "}),compile_command=command))
result=dict(result="PASS_ANDROID_ELF_COMPONENTS",jni=a.jni,targets=targets,apk=False,android_device_execution=False,native_scene_renderer=False,
 scope="Cross-compiled ELF shared libraries and symbol/page-alignment inspection; not installation, runtime, UI or gameplay verification.")
a.report.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!="targets"},indent=2))
for row in targets:print(row["abi"],row["bytes"],"bytes; defined API exports",len(row["api_exports"]),"LOAD alignments",row["load_page_alignments"])
