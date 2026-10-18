#ifndef NF_ORDERED_BUNDLE_H
#define NF_ORDERED_BUNDLE_H
#include <string.h>
#include <math.h>
#include "scene_packet.h"
#include "indexed_copy.h"
typedef struct {uint64_t cycles;uint32_t type,pass,ordinal,kind,source,page;} NFOrderedSceneEvent;
typedef struct {uint64_t epoch;uint32_t event_count,asset_count,camera_count;const uint8_t *events,*directory,*cameras,*data;size_t size;NFScenePacket packet;} NFOrderedBundle;
static uint32_t nf_bundle_word(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
/* Validate the whole borrowed view before exposing any pointer. */
static int nf_ordered_bundle_view(const void*source,size_t size,NFOrderedBundle*out){
 if(!source||!out||size<64||size>32*1024*1024)return 0;
 const uint8_t*p=source;uint32_t h[16];memcpy(h,p,64);
 if(h[0]!=0x424f464e||h[1]!=1||h[5]>1||h[4]<h[3]||!h[6]||h[6]>608||h[7]>32||!h[8]||h[8]>144||!(h[14]|h[15]))return 0;
 size_t end=64+h[6]*32u;if(h[9]!=64||h[10]!=end)return 0;
 end+=h[7]*8u;if(h[11]!=end)return 0;end+=h[8]*56u;if(h[12]!=end||end>size||h[13]>size-end)return 0;
 NFScenePacket packet;if(!nf_scene_packet_view(p+end,h[13],&packet)||packet.serial!=h[2]||packet.begin_refresh!=h[3]||packet.end_refresh!=h[4]||packet.page!=h[5])return 0;
 end+=h[13];unsigned geometry=nf_bundle_word(packet.section[2].data+4),world=nf_bundle_word(packet.section[1].data+4),models=nf_scene_packet_model_count(&packet);
 if(geometry!=h[8])return 0;
 for(unsigned i=0;i<h[8]*7;i++){double d;memcpy(&d,p+h[11]+i*8,8);if(!isfinite(d))return 0;}
 uint32_t kinds[32];
 for(unsigned i=0;i<h[7];i++){
  const uint8_t*entry=p+h[10]+i*8;unsigned offset=nf_bundle_word(entry),bytes=nf_bundle_word(entry+4),page,at;const uint8_t*indices;size_t count;
  if(offset!=end||bytes>size-end||!nf_indexed_operation_view(p+end,bytes,kinds+i,&page,&at,&indices,&count)||page!=h[5])return 0;end+=bytes;
 }if(end!=size)return 0;
 unsigned seen[32]={0},g=0,pass=0,ordinal=0,model_seen=0;uint64_t previous=0;
 for(unsigned i=0;i<h[6];i++){
  NFOrderedSceneEvent e;memcpy(&e,p+h[9]+i*32,32);
  if(!e.cycles||e.cycles<=previous||e.page!=h[5])return 0;previous=e.cycles;
  if(e.type==1||e.type==2){if(e.pass!=UINT32_MAX||e.ordinal>=h[7]||seen[e.ordinal]++||e.kind!=kinds[e.ordinal]||e.type!=e.kind||e.source)return 0;}
  else if(e.type==3||e.type==4){
   /* Explicit pass transitions preserve post-model surfaces in the same pass. */
   if(e.pass!=pass){if(e.pass!=pass+1||model_seen!=pass+1||!ordinal)return 0;pass=e.pass;ordinal=0;}
   if(g>=geometry||e.pass>=models||e.ordinal!=ordinal++)return 0;
   unsigned index=nf_bundle_word(packet.section[2].data+8+g++*4),id;
   if(e.type==4){if(e.kind!=5||model_seen!=pass||index!=UINT32_MAX-model_seen)return 0;id=world+model_seen++;}
   else{if(index>=world||e.kind<1||e.kind>2)return 0;id=index;}
   const uint8_t*identity=packet.section[4].data+8+id*20;
   if(nf_bundle_word(identity)!=(e.type==4?3:e.kind)||nf_bundle_word(identity+8)!=e.source)return 0;
  }else return 0;
 }
 if(g!=geometry||model_seen!=models||pass+1!=models||!ordinal)return 0;for(unsigned i=0;i<h[7];i++)if(seen[i]!=1)return 0;
 NFOrderedBundle v={((uint64_t)h[15]<<32)|h[14],h[6],h[7],h[8],p+h[9],p+h[10],p+h[11],p,size,packet};*out=v;return 1;
}
#endif
