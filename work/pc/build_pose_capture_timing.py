from pathlib import Path
import hashlib,json,shutil,subprocess,os
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');pc=root/'work/pc';base=Path('C:/NFSUG-Workspace');baseline=base/'NFSUG-pc-traffic-refresh2-core';out=base/'NFSUG-pc-pose-capture-timing-tests';source=out/'source'
out.mkdir(exist_ok=True);assert not source.exists(),'Keep diagnostic build inputs immutable'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'traffic-refresh2-build-report.json').read_text());qualified=base/'NFSUG-pc-owner-pose-draw-tests/capture-host.dll'
assert r['core_sha256']==sha(qualified)=='cf66b6edbd86d8cd1261cf59a4e529f9aac821ffe442e4f01dd46de8bfb83f44'
assert shutil.disk_usage('C:/').free>10*1024**3
for name,digest in r['staged_input_sha256'].items():
 p=baseline/'source'/name;assert sha(p)==digest,name;dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
capture=r'''/* Timestamp-only bounded diagnostics. No new ARM hooks or game writes. */
typedef struct {uint64_t epoch,root_cycles[2],model_cycles[2];unsigned serial,root_frame[2],model_frame[2],roots,models;} NFPCPoseCaptureTiming;
static NFPCPoseCaptureTiming nf_pc_pose_capture_ring[16];
static NFPCPoseCaptureTiming*nf_pc_pose_record(void){
 unsigned serial=live_scene.serial;NFPCPoseCaptureTiming*p=nf_pc_pose_capture_ring+serial%16;
 if(p->epoch!=live_scene_epoch||p->serial!=serial){memset(p,0,sizeof(*p));p->epoch=live_scene_epoch;p->serial=serial;}return p;
}
static void nf_pc_pose_render_note(void){
 NFPCPoseCaptureTiming*p=nf_pc_pose_record();unsigned frame=c->frameCounter(c);uint64_t cycles=mTimingGlobalTime(c->timing);
 if(!p->roots){p->root_frame[0]=frame;p->root_cycles[0]=cycles;}p->root_frame[1]=frame;p->root_cycles[1]=cycles;p->roots++;
}
static void nf_pc_pose_model_note(void){
 NFPCPoseCaptureTiming*p=nf_pc_pose_record();unsigned frame=c->frameCounter(c);uint64_t cycles=mTimingGlobalTime(c->timing);
 if(!p->models){p->model_frame[0]=frame;p->model_cycles[0]=cycles;}p->model_frame[1]=frame;p->model_cycles[1]=cycles;p->models++;
}
'''
api=r'''/* Copy original capture identity + the actual selected camera, not emulated pixels.
   out16:epoch,serial,begin,end,query,builder,lastRoot,firstRoot,firstModel,
   lastModel,modelInputCount,rootCount,page,prepared,firstRootCycles,lastRootCycles.
   The exact56-byte NFM2 camera pose is returned alongside the 16 words.
   All validation/conversion precedes output writes. Owner thread only. */
__declspec(dllexport) int nf_pc_source_pose_timing(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,uint64_t*out,size_t bytes,void*camera,size_t camera_bytes){
 if(!c||!out||bytes!=128||!camera||camera_bytes!=56||epoch!=nf_native_scene_epoch()||begin>end)return 0;
 NFCompletedSurfaceAudit*e=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*q=completed_surface_audit[i];if(q&&q->id.epoch==epoch&&q->id.serial==serial&&q->id.begin_refresh==begin&&q->id.end_refresh==end){if(e)return 0;e=q;}}
 NFPCPoseCaptureTiming*p=nf_pc_pose_capture_ring+serial%16;
 if(!e||!e->render_snapshot||p->epoch!=epoch||p->serial!=serial||!p->roots||!p->models)return 0;
 uint32_t view[12];unsigned prepared=nf_visibility_snapshot_prepared_view(e->render_snapshot,view);
 if(!prepared){NFVisibilityPoseInputs pose;if(!nf_live_completed_visibility_pose(epoch,serial,begin,end,&pose))return 0;memcpy(view,pose.view,48);}
 NFPoint3 position={-(double)(int32_t)view[9],-(double)(int32_t)view[10],-(double)(int32_t)view[11]};NFRigidPose pose;
 if(!nf_pose_decode((const int32_t*)view,&position,&pose))return 0;
 uint64_t words[16]={epoch,serial,begin,end,e->id.query_refresh,e->id.builder_refresh,p->root_frame[1],p->root_frame[0],p->model_frame[0],p->model_frame[1],p->models,p->roots,e->page,prepared,p->root_cycles[0],p->root_cycles[1]};
 memcpy(out,words,128);memcpy(camera,&pose,56);return 1;
}
'''
(source/'pose_capture_timing_probe.inc').write_text(capture);(source/'pose_capture_timing_api.inc').write_text(api)
p=source/'camera/live_visibility.h';text=p.read_text();marker='static void live_model_inputs_draw(void){';assert text.count(marker)==1;text=text.replace(marker,'#include "../pose_capture_timing_probe.inc"\n'+marker)
marker='pending_model_inputs.models[n]=item;pending_model_inputs.count++;';assert text.count(marker)==1;text=text.replace(marker,marker+'nf_pc_pose_model_note();')
marker='free(ram);\n\n  /* Compare query-time ownership';assert text.count(marker)==1;text=text.replace(marker,'free(ram);if(render_snapshot_pending)nf_pc_pose_render_note();\n\n  /* Compare query-time ownership')
p.write_text(text)
with (source/'observer.c').open('a') as f:f.write('\n#include "pose_capture_timing_api.inc"\n')
cmd=[a.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;'+env['PATH']
result=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=240);(out/'build.log').write_text(result.stdout+result.stderr);print('compile',result.returncode,flush=True);result.check_returncode()
report={'result':'BUILT_READONLY_POSE_CAPTURE_TIMING_DIAGNOSTIC','core_sha256':sha(out/'capture-host.dll'),'baseline_core_sha256':sha(qualified),'baseline_factory_sha256':sha(baseline/'traffic-refresh2-build-report.json'),'command':cmd,'original_staged_sha256':r['staged_input_sha256'],'staged_sha256':{str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},'new_files_sha256':{n:sha(source/n) for n in ['pose_capture_timing_probe.inc','pose_capture_timing_api.inc']},'game_hooks_added':False,'game_writes_added':False,'shipping_changed':False,'builder_sha256':sha(Path(__file__))}
(out/'timing-build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['command','staged_sha256','original_staged_sha256']}))
for n in ['pose_capture_timing_probe.inc','pose_capture_timing_api.inc']:shutil.copyfile(source/n,pc/n)
shutil.copyfile(Path(__file__),pc/'build_pose_capture_timing.py')
