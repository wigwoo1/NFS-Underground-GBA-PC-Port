/* Copy original capture identity + the actual selected camera, not emulated pixels.
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
