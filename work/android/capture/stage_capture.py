"""Stage a borrowed-core observer without changing authoritative PC/app sources."""
from pathlib import Path
import argparse,hashlib,json,re
a=argparse.ArgumentParser();a.add_argument("--output",type=Path,required=True);a=a.parse_args()
here=Path(__file__).resolve().parent;root=here.parents[2];work=root/"work"
a.output.mkdir(parents=True,exist_ok=True);src=a.output/"source";src.mkdir(exist_ok=True)
names=(work/"v2/package/NFSUG-Native-Renderer-source/camera/native-renderer-sources.txt").read_text().splitlines()
names=[n for n in names if n and not n.startswith("#") and n!="packet_preview.c"]
queue=["camera/"+n for n in names]+["probe.c","v2/scene.h"];copied={}
while queue:
 name=queue.pop()
 if name in copied:continue
 data=(work/name).read_bytes();target=src/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 copied[name]=hashlib.sha256(data).hexdigest()
 for inc in re.findall(r'^\s*#include\s+"([^"]+)"',data.decode("utf-8",errors="ignore"),re.M):
  if inc=="../outputs/nfsug-research/native_span.h":continue
  child=(Path(name).parent/inc).as_posix();assert ".." not in Path(child).parts;queue.append(child)
for name in ("native_span.h","native_span.c"):
 data=(work/"v2/package/NFSUG-Native-Renderer-source"/name).read_bytes();(src/name).write_bytes(data);copied[name]=hashlib.sha256(data).hexdigest()
text=(src/"probe.c").read_text(encoding="utf-8").replace('"../outputs/nfsug-research/native_span.h"','"native_span.h"')
begin=text.index("API int nf_init(");end=text.index("\nAPI void nf_60",begin);init=text[begin:end]
hooks=init[init.index("struct ARMCore* cpu=c->cpu;"):init.index(" if(trace_fileile")]
text=text[:begin]+text[end:]
old="if(c){mCoreConfigDeinit(&c->config);c->deinit(c);c=NULL;}";assert text.count(old)==1
text=text.replace(old,"c=NULL;",1).replace("static uint32_t pixels[240*160];","static uint32_t*pixels;",1)
text+=(here/"observer_adapter.inc").read_text(encoding="utf-8").replace("@INSTALL_ORIGINAL_HOOKS@",hooks)
(src/"observer.c").write_text(text,encoding="utf-8")
layer=src/"camera/layer_snapshot.c"
with layer.open("a",encoding="utf-8") as target:target.write((here/"layer_pack.inc").read_text(encoding="utf-8"))
(src/"nfsug_android_jni.c").write_bytes((work/"android/nfsug_android_jni.c").read_bytes())
data=(work/"android/nfsug_android_core.h").read_bytes();(src/"nfsug_android_core.h").write_bytes(data)
text=(work/"android/nfsug_android_core.c").read_text(encoding="utf-8")
decl="int nf_android_observer_source_world_enable(int);\nsize_t nf_android_observer_source_world(uint64_t,unsigned,unsigned,unsigned,void*,size_t);\nsize_t nf_android_observer_bundle(uint64_t,unsigned,void*,size_t);\nint nf_android_observer_attach(struct mCore*,uint32_t*);\nvoid nf_android_observer_detach(void);\nvoid nf_android_observer_boundary(void);\nvoid nf_android_observer_reset(void);\nsize_t nf_android_observer_owned_packet(uint64_t,unsigned,void*,size_t);\nint nf_android_observer_split(unsigned,uint64_t[12]);\nsize_t nf_android_observer_provenance(uint64_t,unsigned,void*,size_t);\nint nf_android_observer_display_owner(unsigned,uint64_t[8]);\nint nf_android_observer_pair(unsigned,uint64_t[8]);\nint nf_android_observer_layers(int);\nint nf_android_observer_layer_info(uint64_t[5]);\nsize_t nf_android_observer_layer_row(uint64_t,unsigned,unsigned,void*,size_t);\nsize_t nf_android_observer_copy(void*,size_t);\nvoid nf_android_observer_stats(uint64_t[8]);\nstruct NFAAndroidCore {struct mCore*core;int capture;"
needle="struct NFAAndroidCore {struct mCore*core;";assert text.count(needle)==1;text=text.replace(needle,decl,1)
needle="struct mCore*c=s->core;active_core=NULL;";assert text.count(needle)==1
text=text.replace(needle,"if(s->capture)nf_android_observer_detach();\n struct mCore*c=s->core;active_core=NULL;",1)
needle="c->setKeys(c,keys);c->runFrame(c);";assert text.count(needle)==1
text=text.replace(needle,"if(s->capture)nf_android_observer_boundary();\n c->setKeys(c,keys);c->runFrame(c);\n if(s->capture)nf_android_observer_boundary();",1)
needle="s->core->setKeys(s->core,0);s->steps=0;";assert text.count(needle)==1
text=text.replace(needle,"if(s->capture)nf_android_observer_reset();\n s->core->setKeys(s->core,0);s->steps=0;",1)
text+=(here/"core_capture_api.inc").read_text(encoding="utf-8")
(src/"nfsug_android_core.c").write_text(text,encoding="utf-8")
for name in ("windows.h","CMakeLists.txt"):(src/name).write_bytes((here/name).read_bytes())
(src/"capture_sources.cmake").write_text("set(NF_CAPTURE_SOURCES\n"+"\n".join(' "camera/'+n+'"' for n in names)+"\n)\n")
(a.output/"source-provenance.json").write_text(json.dumps({"authoritative":str(root),"unaltered_source_sha256":copied,"cpu_sources":names,"stage_only_probe_transform":True,"staged_layer_extension":{"path":"camera/layer_snapshot.c","extension":"work/android/capture/layer_pack.inc","extension_sha256":hashlib.sha256((here/"layer_pack.inc").read_bytes()).hexdigest(),"staged_sha256":hashlib.sha256((src/"camera/layer_snapshot.c").read_bytes()).hexdigest()},"app_source_changed":False},indent=2))
print("Staged borrowed-core observer with",len(copied),"hash-recorded shared files",flush=True)

# Reuse the PC producer verified on the same ROM/state and scene848.
# These are exact maintained source bytes; only an include path is normalized.
traffic_sources={
 "traffic_rotation_refresh2_capture.inc":"be24b888113c8fa943dd20c0bac26483ac24b191e0f87fd06cbc48cc0ab2d97c",
 "traffic_rotation_draw_pose.inc":"0ecd30292cee04072234d9c637fca3f76cd2a436c91e3e19e6cb8aebd7b3be84",
}
traffic_inputs={}
for name,digest in traffic_sources.items():
 data=(work/"pc"/name).read_bytes();assert hashlib.sha256(data).hexdigest()==digest,"Unverified traffic producer source: "+name
 traffic_inputs["work/pc/"+name]=digest
 if name=="traffic_rotation_refresh2_capture.inc":
  text=data.decode("utf8");needle='#include "../traffic_rotation_draw_pose.inc"';assert text.count(needle)==1;data=text.replace(needle,'#include "traffic_rotation_draw_pose.inc"').encode("utf8")
 (src/name).write_bytes(data)
header=src/"camera/live_scene.h";text=header.read_text()
def traffic_replace(old,new):
 global text
 assert text.count(old)==1,old
 text=text.replace(old,new,1)
traffic_replace('struct {unsigned address,frame;int32_t matrix[12];} rotations[16];','struct {unsigned address,frame;int32_t matrix[12];unsigned traffic,traffic_object,traffic_camera,traffic_serial;uint64_t traffic_epoch;int32_t traffic_cm[12],traffic_actual[9],traffic_draw_cm[12];unsigned traffic_draw_frame,traffic_draw_bound;} rotations[16];')
traffic_replace('static void native_scene_event(struct ARMCore*cpu,unsigned pc){','#include "../traffic_rotation_refresh2_capture.inc"\nstatic void native_scene_event(struct ARMCore*cpu,unsigned pc){')
traffic_replace('static void native_scene_event(struct ARMCore*cpu,unsigned pc){\n if(!live_scene.assembly)return;','static void native_scene_event(struct ARMCore*cpu,unsigned pc){\n if(!live_scene.assembly)return;\n if(nf_traffic_event(cpu,pc))return;')
traffic_replace('live_scene.rotations[i].address=r[2];live_scene.rotations[i].frame=c->frameCounter(c);','live_scene.rotations[i].address=r[2];live_scene.rotations[i].frame=c->frameCounter(c);live_scene.rotations[i].traffic=0;')
traffic_replace('live_scene.rotations[i].frame<=frame){','live_scene.rotations[i].frame<=frame&&nf_traffic_rotation_valid(i,live_scene.camera,live_scene.object)){')
assert text.count('live_scene_epoch++;')==2
text=text.replace('live_scene_epoch++;','nf_traffic_reset();live_scene_epoch++;');header.write_text(text)
header=src/"camera/live_visibility.h";text=header.read_text();needle='live_scene.rotations[i].frame<=frame){';assert text.count(needle)==1
header.write_text(text.replace(needle,'live_scene.rotations[i].frame<=frame&&nf_traffic_rotation_valid(i,live_scene.camera,live_scene.object)){',1))
with (src/"observer.c").open("a",encoding="utf8") as stream:
 stream.write('\n__declspec(dllexport) int nf_android_traffic_rotation_stats(uint64_t out[6]){if(!c||!out)return 0;memcpy(out,nf_traffic_stats,48);return 1;}\n')
report_path=a.output/"source-provenance.json";provenance=json.loads(report_path.read_text())
provenance["staged_traffic_extension"]={"reference":"PC exact traffic products/draw-camera/two-stage single-refresh producer","maintained_source_sha256":traffic_inputs,"staged_sha256":{name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in ["traffic_rotation_refresh2_capture.inc","traffic_rotation_draw_pose.inc","camera/live_scene.h","camera/live_visibility.h","observer.c"]},"game_logic_changed":False}
report_path.write_text(json.dumps(provenance,indent=2))
print("Staged verified PC traffic producer; object/slot/camera/epoch/scene guards retained")
