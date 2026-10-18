/* Maintained immutable packet transfer ABI. Provider DLL must outlive all frames. */

size_t nf_android_observer_background_take(uint64_t epoch,unsigned refresh,void**owned){
 if(!owned)return 0;*owned=NULL;uint8_t*packet=NULL;
 size_t bytes=android_background_scene_owned(epoch,refresh,&packet);
 if(!bytes)return 0;*owned=packet;return bytes;
}

size_t nf_android_observer_source_world_take(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void**owned){
 if(!owned)return 0;*owned=NULL;
 if(!c||!android_source_world||epoch!=nf_native_scene_epoch()||begin>end)return 0;
 void*packet=NULL;size_t bytes=0;unsigned stage;
 if(!nf_live_completed_native_multimodel_world_classified_owned(epoch,serial,begin,end,&packet,&bytes,&stage))return 0;
 if(!packet||!bytes){nf_scene_packet_free(packet);return 0;}*owned=packet;return bytes;
}
void nf_android_observer_source_world_free(void*packet){nf_scene_packet_free(packet);}
