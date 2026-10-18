/* Diagnostic only: candidate-140 packet has one appended unlit wall.
   Bounds must come from the sampled draw-plan report; no live policy. */
#include "scene_packet.h"
static void candidate_portal_clip(int ring);
static void candidate_packet_select(const NFScenePacket*p);
static int candidate_ring=-1;
#define NF_DIAGNOSTIC_PACKET_SELECT candidate_packet_select
#define NF_DIAGNOSTIC_DEPTH
#define NF_DIAGNOSTIC_SURFACE_CLIP candidate_portal_clip
#include "packet_preview.c"
static void candidate_portal_clip(int ring){
 if(ring<0){glDisable(GL_SCISSOR_TEST);return;}
 if(ring!=candidate_ring)return;
 int l,r,t,b;char tail;const char*value=getenv("NF_CANDIDATE_PORTAL");
 glEnable(GL_SCISSOR_TEST);
 if(!value||sscanf(value,"%d,%d,%d,%d%c",&l,&r,&t,&b,&tail)!=4||l<0||r>240||t<0||b>160||r<=l||b<=t){glScissor(0,0,0,0);return;}
 /* Pixel-center coverage in the 3240x2160 original-aspect viewport. */
 int x0=(int)ceil(300+l*13.5-.5),x1=(int)ceil(300+r*13.5-.5);
 int y0=(int)ceil((160-b)*13.5-.5),y1=(int)ceil((160-t)*13.5-.5);
 glScissor(x0,y0,x1-x0,y1-y0);
}

static void candidate_packet_select(const NFScenePacket*p){
 candidate_ring=-1;
 /* Only the older augmented fixture needs insertion control. At the exact
    newer endpoint the original captured wall remains untouched. */
 if(p->serial!=140)return;
 uint32_t count;memcpy(&count,p->section[1].data+4,4);
 const uint32_t wanted[5]={2,50331840,139937176,37,0};unsigned matches=0;
 for(unsigned i=0;i<count;i++)if(!memcmp(p->section[4].data+8+i*20,wanted,20)){candidate_ring=(int)i;matches++;}
 if(matches!=1)candidate_ring=-1;
}
