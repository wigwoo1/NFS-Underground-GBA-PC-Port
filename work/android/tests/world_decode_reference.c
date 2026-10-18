#undef __declspec
#define __declspec(x)
#include "scene_packet.c"
#include "snapshot_store.c"
#include "presentation_timeline.c"
__attribute__((dllexport)) int world_reference(const void*data,size_t size,uint32_t*out,unsigned capacity){
 NFScenePacket packet;if(!out||capacity<1028||!nf_scene_packet_view(data,size,&packet))return 0;
 NFWorldMetadata metadata[128];unsigned count;if(!nf_scene_world_metadata_all(packet.section[1],metadata,128,&count))return 0;
 out[0]=count;out[1]=nf_scene_packet_model_count(&packet);out[2]=word(packet.section[2].data+4);out[3]=0;
 size_t light=8;
 for(unsigned i=0;i<count;i++){NFSceneSection surface;if(!nf_scene_world_surface(packet.section[1],i,&surface))return 0;unsigned at=4+i*8;
  out[at]=word(surface.data);out[at+1]=word(surface.data+4);out[at+2]=word(surface.data+8);out[at+3]=surface.size;out[at+4]=metadata[i].mode;out[at+5]=metadata[i].size;out[at+6]=word(packet.section[4].data+8+i*20);out[at+7]=word(packet.section[3].data+light);light+=4;if(out[at+7])light+=16+(size_t)out[at+1]*out[at+2]*64;
 }return 1;
}
