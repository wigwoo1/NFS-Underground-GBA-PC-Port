#ifndef NF_PREPARED_MOTION_SUBMISSION_H
#define NF_PREPARED_MOTION_SUBMISSION_H
#include <stdlib.h>
#include <stdio.h>
#include <windows.h>
#include "road_bundle.h"
#include "owned_road_source.h"
#include "rigid_motion.h"
#include "hud_submission.h"
#include "stable_scene_submission.h"
/* Original event clocks are retained in both complete sources, never assigned
   to reconstructed geometry. Renderer integration must consume sampled order
   separately and account for every original effect. Single-pass proof for now. */
typedef struct {NFHudRowPool*hud_pool;NFOwnedRoadSource*shared_older,*shared_newer;double alpha;size_t older_size,newer_size,packet_size;unsigned camera_count;const uint8_t*older,*newer,*packet;const NFRigidPose*cameras;const uint8_t*hud,*text;size_t hud_size,text_size;unsigned hud_cut,hud_refresh,hud_stable;NFPagePersistenceProof hud_proof;uint64_t occurrence_hash;unsigned occurrence_count;uint32_t occurrences[144][13];unsigned road_count;struct {unsigned command;const uint8_t*data;size_t size;} roads[144];} NFPreparedMotionSubmission;
static void nf_prepared_motion_destroy(NFPreparedMotionSubmission*s){if(s){free(s->hud_pool);nf_owned_road_source_release(s->shared_older);nf_owned_road_source_release(s->shared_newer);free(s);}}
static uint32_t nf_occurrence_match_detail[4];
static int nf_prepared_motion_occurrences_match(const NFPreparedMotionSubmission*s,const uint32_t*rows,unsigned n){
 nf_occurrence_match_detail[0]=1;NFScenePacket p;double alpha;const uint8_t*bounds,*model_bounds;if(!s||!rows||!n||n>144||n!=s->camera_count||!nf_scene_packet_view(s->packet,s->packet_size,&p)||nf_bundle_word(p.section[2].data+4)!=n||!nf_scene_packet_bounds(&p,&alpha,&bounds)||alpha!=(s->alpha==1?0:s->alpha)||!nf_scene_packet_model_bounds(&p,&model_bounds))return 0;
 nf_occurrence_match_detail[0]=2;unsigned world=nf_bundle_word(p.section[1].data+4),models=nf_scene_packet_model_count(&p);
 for(unsigned i=0;i<n;i++){unsigned index=nf_bundle_word(p.section[2].data+8+i*4),model=UINT32_MAX-index;const uint32_t*r=rows+i*13;nf_occurrence_match_detail[1]=i;nf_occurrence_match_detail[2]=r[0];nf_occurrence_match_detail[3]=r[1];const uint8_t*clip;if(index<world)clip=bounds+index*8;else{if(model>=models)return 0;index=world+model;clip=model_bounds+model*8;}const uint8_t*id=p.section[4].data+8+index*20;if(nf_bundle_word(id)!=(r[0]==5?3:r[0])||nf_bundle_word(id+8)!=r[1])return 0;for(unsigned j=0;j<4;j++){uint16_t v;memcpy(&v,clip+j*2,2);if(v!=r[9+j]){nf_occurrence_match_detail[0]=3;if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("motion_occurrence_clip_mismatch command=%u axis=%u packet=%u row=%u\n",i,j,v,r[9+j]);return 0;}}}
 return 1;
}
/* Copy producer provenance before queue publication. Strict geometry policy is unchanged. */
static uint64_t nf_prepared_motion_occurrence_hash(const uint32_t*rows,unsigned n){uint64_t h=14695981039346656037ull;const uint8_t*p=(const uint8_t*)rows;for(size_t i=0;i<(size_t)n*13*4;i++){h^=p[i];h*=1099511628211ull;}return h;}
static int nf_prepared_motion_occurrences_valid(const NFPreparedMotionSubmission*s){return s&&s->occurrence_count&&s->occurrence_count<=144&&s->occurrence_hash==nf_prepared_motion_occurrence_hash(&s->occurrences[0][0],s->occurrence_count)&&nf_prepared_motion_occurrences_match(s,&s->occurrences[0][0],s->occurrence_count);}
static int nf_prepared_motion_occurrence_same_draw(const uint32_t*a,const uint32_t*b){return a&&b&&a[0]==b[0]&&a[1]==b[1]&&a[3]==b[3]&&!memcmp(a+5,b+5,8*sizeof(*a));}
static int nf_prepared_motion_attach_occurrences(NFPreparedMotionSubmission*s,const uint32_t*rows,unsigned n){
 NFScenePacket packet;if(!nf_prepared_motion_occurrences_match(s,rows,n)||!s||!rows||s->occurrence_count||!n||n>144||n!=s->camera_count||!nf_scene_packet_view(s->packet,s->packet_size,&packet)||nf_bundle_word(packet.section[4].data+4)!=n)return 0;
 for(unsigned i=0;i<n;i++){const uint32_t*r=rows+i*13;unsigned source_count=0,packet_count=0;for(unsigned j=0;j<n;j++){const uint32_t*other=rows+j*13;const uint8_t*id=packet.section[4].data+8+j*20;if(other[0]==r[0]&&other[1]==r[1])source_count++;if(nf_bundle_word(id)==(r[0]==5?3:r[0])&&nf_bundle_word(id+8)==r[1])packet_count++;/* Owner/mask counters cannot make a copied draw occurrence distinct. */ if(j<i&&nf_prepared_motion_occurrence_same_draw(r,other))return 0;}if(!packet_count||source_count!=packet_count)return 0;}
 memcpy(s->occurrences,rows,n*13*sizeof(*rows));s->occurrence_count=n;s->occurrence_hash=nf_prepared_motion_occurrence_hash(rows,n);return 1;
}
/* Immutable shared bytes were canonical-validated at creation. A queued owner
   holds both references; no simulation/DLL/producer pointer is consulted. */
static int nf_prepared_motion_source_views(const NFPreparedMotionSubmission*s,NFRoadBundle*out_a,NFRoadBundle*out_b){
 if(!s||!out_a||!out_b)return 0;NFRoadBundle a,b;
 if(s->shared_older||s->shared_newer){const NFOwnedRoadSource*x=s->shared_older,*y=s->shared_newer;if(!x||!y||s->older!=x->bytes||s->newer!=y->bytes||s->older_size!=x->size||s->newer_size!=y->size||x->epoch!=y->epoch||x->observer_version!=y->observer_version)return 0;a=x->view;b=y->view;}
 else if(!nf_road_bundle_view(s->older,s->older_size,&a)||!nf_road_bundle_view(s->newer,s->newer_size,&b))return 0;
 *out_a=a;*out_b=b;return 1;
}
static int nf_motion_prefix_only(const NFOrderedBundle*b){unsigned geometry=0;for(unsigned i=0;i<b->event_count;i++){NFOrderedSceneEvent e;memcpy(&e,b->events+i*32,32);if(e.type>=3)geometry=1;else if(geometry)return 0;}return 1;}
/* Internal canonical views: exclusive call-scope validation or immutable owned source. */
static int nf_prepared_motion_geometry_canonical_rows(NFRoadBundle av,NFRoadBundle bv,const void*p,size_t pn,const NFRigidPose*c,unsigned cn,double alpha,const uint32_t*rows){
 NFScenePacket packet;if(!c||!isfinite(alpha)||alpha<0||alpha>1||!nf_scene_packet_view(p,pn,&packet))return 0;
 const NFOrderedBundle*x=&av.ordered,*y=&bv.ordered,*basis=alpha==1?y:x;
 if(!nf_motion_prefix_only(x)||!nf_motion_prefix_only(y)){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("motion_owner_rejection older=%u newer=%u reason=prefix_order older_prefix=%d newer_prefix=%d\n",x->packet.serial,y->packet.serial,nf_motion_prefix_only(x),nf_motion_prefix_only(y));return 0;}
 if(x->epoch!=y->epoch||x->packet.serial>=y->packet.serial||packet.serial!=basis->packet.serial||packet.begin_refresh!=basis->packet.begin_refresh||packet.end_refresh!=basis->packet.end_refresh||packet.page!=basis->packet.page||nf_scene_packet_model_count(&packet)!=1||nf_scene_packet_model_count(&x->packet)!=1||nf_scene_packet_model_count(&y->packet)!=1||!nf_motion_prefix_only(x)||!nf_motion_prefix_only(y)||!cn||cn>144||nf_bundle_word(packet.section[2].data+4)!=cn)return 0;
 for(unsigned i=0;i<cn*7;i++){double v;memcpy(&v,(const uint8_t*)c+i*8,8);if(!isfinite(v))return 0;}
 unsigned world=nf_bundle_word(packet.section[1].data+4);
 NFPreparedMotionSubmission occurrence_owner={0};if(rows){occurrence_owner.packet=p;occurrence_owner.packet_size=pn;occurrence_owner.camera_count=cn;occurrence_owner.alpha=alpha;if(!nf_prepared_motion_attach_occurrences(&occurrence_owner,rows,cn)){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("motion_occurrence_constructor_rejection stage=%u command=%u kind=%u source=%u alpha=%.17g\n",nf_occurrence_match_detail[0],nf_occurrence_match_detail[1],nf_occurrence_match_detail[2],nf_occurrence_match_detail[3],alpha);return 0;}}
 for(unsigned i=0;i<world+1;i++){const uint8_t*id=packet.section[4].data+8+i*20;unsigned kind=nf_bundle_word(id),source=nf_bundle_word(id+8),matches=0;
  for(unsigned j=0;j<i;j++){const uint8_t*prior=packet.section[4].data+8+j*20;if(kind==nf_bundle_word(prior)&&source==nf_bundle_word(prior+8)&&(!rows||kind==3)){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("motion_geometry_rejection older=%u newer=%u reason=duplicate identity=%u prior=%u kind=%u source=%u\n",x->packet.serial,y->packet.serial,i,j,kind,source);return 0;}}
  const NFScenePacket*endpoints[2]={&x->packet,&y->packet};for(unsigned e=0;e<2;e++){unsigned n=nf_bundle_word(endpoints[e]->section[1].data+4)+1;for(unsigned j=0;j<n;j++){const uint8_t*q=endpoints[e]->section[4].data+8+j*20;matches+=kind==nf_bundle_word(q)&&source==nf_bundle_word(q+8);}}
  if(!matches){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("motion_geometry_rejection older=%u newer=%u reason=unowned identity=%u kind=%u source=%u\n",x->packet.serial,y->packet.serial,i,kind,source);return 0;}
 }
 if(alpha==0||alpha==1){size_t endpoint_size=nf_bundle_word(basis->data+52);const uint8_t*endpoint=basis->data+nf_bundle_word(basis->data+48);if(pn!=endpoint_size||memcmp(p,endpoint,pn)||cn!=basis->camera_count||memcmp(c,basis->cameras,cn*56))return 0;}
 return 1;
}
static int nf_prepared_motion_geometry_canonical(NFRoadBundle a,NFRoadBundle b,const void*p,size_t pn,const NFRigidPose*c,unsigned cn,double alpha){return nf_prepared_motion_geometry_canonical_rows(a,b,p,pn,c,cn,alpha,NULL);}
static int nf_prepared_motion_geometry_views(const void*a,size_t an,const void*b,size_t bn,const void*p,size_t pn,const NFRigidPose*c,unsigned cn,double alpha,NFRoadBundle*out_a,NFRoadBundle*out_b){NFRoadBundle av,bv;if(!nf_road_bundle_view(a,an,&av)||!nf_road_bundle_view(b,bn,&bv)||!nf_prepared_motion_geometry_canonical(av,bv,p,pn,c,cn,alpha))return 0;if(out_a)*out_a=av;if(out_b)*out_b=bv;return 1;}
static int nf_prepared_motion_geometry_valid(const void*a,size_t an,const void*b,size_t bn,const void*p,size_t pn,const NFRigidPose*c,unsigned cn,double alpha){return nf_prepared_motion_geometry_views(a,an,b,bn,p,pn,c,cn,alpha,NULL,NULL);}
static int nf_prepared_motion_create(const void*a,size_t an,const void*b,size_t bn,const void*p,size_t pn,const NFRigidPose*c,unsigned cn,double alpha,NFPreparedMotionSubmission**out){
 if(!out||!nf_prepared_motion_geometry_valid(a,an,b,bn,p,pn,c,cn,alpha))return 0;
 size_t total=sizeof(NFPreparedMotionSubmission)+an+bn+pn+cn*sizeof(*c);NFPreparedMotionSubmission*s=calloc(total,1);if(!s)return 0;uint8_t*q=(uint8_t*)(s+1);s->cameras=(const NFRigidPose*)q;memcpy(q,c,cn*sizeof(*c));q+=cn*sizeof(*c);s->alpha=alpha;s->older_size=an;s->newer_size=bn;s->packet_size=pn;s->camera_count=cn;s->older=q;memcpy(q,a,an);q+=an;s->newer=q;memcpy(q,b,bn);q+=bn;s->packet=q;memcpy(q,p,pn);q+=pn;*out=s;return 1;
}

/* Live use requires both source-derived alpha and actual displayed HUD refresh.
   Diagnostic fixed-refresh phase sweeps intentionally fail this gate. */
/* These views must be canonical and belong to this immutable owner. */
static int nf_prepared_motion_clock_views(const NFPreparedMotionSubmission*s,const NFTimelineSample*t,const NFRoadBundle*a,const NFRoadBundle*b){
 if(!s||!t||!a||!b||(!s->hud&&!s->hud_pool)||!isfinite(t->target)||!isfinite(t->alpha))return 0;
 double begin=a->ordered.packet.end_refresh,end=b->ordered.packet.end_refresh;if(end<=begin||t->epoch!=a->ordered.epoch||t->older!=a->ordered.packet.serial||t->newer!=b->ordered.packet.serial||t->target<begin||t->target>end||floor(t->target)!=s->hud_refresh)return 0;double alpha=(t->target-begin)/(end-begin);return fabs(alpha-s->alpha)<=1e-12&&fabs(alpha-t->alpha)<=1e-12;
}
static int nf_prepared_motion_clock_valid(const NFPreparedMotionSubmission*s,const NFTimelineSample*t){NFRoadBundle a,b;return nf_prepared_motion_source_views(s,&a,&b)&&nf_prepared_motion_clock_views(s,t,&a,&b);}
typedef struct {unsigned command;const void*data;size_t size;} NFPreparedRoadAttachment;
static int nf_prepared_motion_roads_valid(const NFPreparedMotionSubmission*s,const NFPreparedRoadAttachment*roads,unsigned count,size_t*out_extra){
 if(!s||!out_extra||count>144||(count&&!roads))return 0;NFScenePacket p;if(!nf_scene_packet_view(s->packet,s->packet_size,&p))return 0;
 nf_occurrence_match_detail[0]=2;unsigned world=nf_bundle_word(p.section[1].data+4);size_t extra=0;
 for(unsigned i=0;i<count;i++){NFRoadAssetView v;unsigned command=roads[i].command;if(command>=s->camera_count||!nf_road_asset_view(roads[i].data,roads[i].size,&v)||v.header[2]!=p.serial||v.header[3]!=0||v.header[4]!=command)return 0;for(unsigned j=0;j<i;j++)if(command==roads[j].command)return 0;unsigned index=nf_bundle_word(p.section[2].data+8+command*4);if(index>=world||nf_bundle_word(p.section[4].data+8+index*20)!=1||nf_bundle_word(p.section[4].data+8+index*20+12)!=8)return 0;if(roads[i].size>64*1024*1024-extra)return 0;extra+=roads[i].size;}
 *out_extra=extra;return 1;
}
/* Atomically replace exclusive owner; source assets are copied, never adopted. */
static int nf_prepared_motion_attach_roads(NFPreparedMotionSubmission**owner,const NFPreparedRoadAttachment*roads,unsigned count){
 if(!owner||!*owner||!roads||!count||count>144||(*owner)->road_count||(*owner)->hud||(*owner)->shared_older||(*owner)->shared_newer)return 0;NFPreparedMotionSubmission*s=*owner;NFScenePacket p;if(!nf_scene_packet_view(s->packet,s->packet_size,&p))return 0;
 size_t extra;if(!nf_prepared_motion_roads_valid(s,roads,count,&extra))return 0;
 size_t bytes=sizeof(*s)+s->camera_count*sizeof(NFRigidPose)+s->older_size+s->newer_size+s->packet_size;NFPreparedMotionSubmission*n=malloc(bytes+extra);if(!n)return 0;memcpy(n,s,bytes);
 n->older=(uint8_t*)n+(s->older-(uint8_t*)s);n->newer=(uint8_t*)n+(s->newer-(uint8_t*)s);n->packet=(uint8_t*)n+(s->packet-(uint8_t*)s);n->cameras=(NFRigidPose*)((uint8_t*)n+((uint8_t*)s->cameras-(uint8_t*)s));uint8_t*q=(uint8_t*)n+bytes;
 for(unsigned i=0;i<count;i++){n->roads[i].command=roads[i].command;n->roads[i].data=q;n->roads[i].size=roads[i].size;memcpy(q,roads[i].data,roads[i].size);q+=roads[i].size;}n->road_count=count;free(s);*owner=n;return 1;
}

static int nf_prepared_motion_attach_display(NFPreparedMotionSubmission**owner,const void*hud,size_t hs,const void*text,size_t ts,unsigned cut,const NFPagePersistenceProof*proof){
 if(!owner||!*owner||(*owner)->hud||(*owner)->shared_older||(*owner)->shared_newer)return 0;NFPreparedMotionSubmission*s=*owner;NFRoadBundle a,b;NFHudSubmissionView view;if(!nf_road_bundle_view(s->older,s->older_size,&a)||!nf_road_bundle_view(s->newer,s->newer_size,&b)||(proof?!nf_stable_scene_view(s->older,s->older_size,hud,hs,text,ts,proof,&view):!nf_hud_submission_view(&a,&b,hud,hs,text,ts,cut,&view)))return 0;
 size_t bytes=sizeof(*s)+s->camera_count*sizeof(NFRigidPose)+s->older_size+s->newer_size+s->packet_size;for(unsigned i=0;i<s->road_count;i++)bytes+=s->roads[i].size;
 NFPreparedMotionSubmission*n=malloc(bytes+hs+ts);if(!n)return 0;memcpy(n,s,bytes);
 n->older=(uint8_t*)n+(s->older-(uint8_t*)s);n->newer=(uint8_t*)n+(s->newer-(uint8_t*)s);n->packet=(uint8_t*)n+(s->packet-(uint8_t*)s);n->cameras=(NFRigidPose*)((uint8_t*)n+((uint8_t*)s->cameras-(uint8_t*)s));for(unsigned i=0;i<s->road_count;i++)n->roads[i].data=(uint8_t*)n+(s->roads[i].data-(uint8_t*)s);
 n->hud=(uint8_t*)n+bytes;n->text=n->hud+hs;n->hud_size=hs;n->text_size=ts;n->hud_cut=proof?160:cut;n->hud_refresh=view.refresh;n->hud_stable=proof!=NULL;if(proof)n->hud_proof=*proof;memcpy((void*)n->hud,hud,hs);memcpy((void*)n->text,text,ts);free(s);*owner=n;return 1;
}

/* One replacement allocation for complete sampled roads and actual stable HUD.
   Validation finishes before allocation or mutation; failure retains the owner. */
static int nf_prepared_motion_attach_complete(NFPreparedMotionSubmission**owner,const NFPreparedRoadAttachment*roads,unsigned count,const void*hud,size_t hs,const void*text,size_t ts,const NFPagePersistenceProof*proof){
 if(!owner||!*owner||!proof||(*owner)->road_count||(*owner)->hud||(*owner)->shared_older||(*owner)->shared_newer)return 0;NFPreparedMotionSubmission*s=*owner;size_t extra;NFHudSubmissionView view;
 if(!nf_prepared_motion_roads_valid(s,roads,count,&extra)||!nf_stable_scene_view(s->older,s->older_size,hud,hs,text,ts,proof,&view))return 0;
 size_t bytes=sizeof(*s)+s->camera_count*sizeof(NFRigidPose)+s->older_size+s->newer_size+s->packet_size;
 if(extra>SIZE_MAX-bytes||hs>SIZE_MAX-bytes-extra||ts>SIZE_MAX-bytes-extra-hs)return 0;
 NFPreparedMotionSubmission*n=malloc(bytes+extra+hs+ts);if(!n)return 0;memcpy(n,s,bytes);
 n->older=(uint8_t*)n+(s->older-(uint8_t*)s);n->newer=(uint8_t*)n+(s->newer-(uint8_t*)s);n->packet=(uint8_t*)n+(s->packet-(uint8_t*)s);n->cameras=(NFRigidPose*)((uint8_t*)n+((uint8_t*)s->cameras-(uint8_t*)s));uint8_t*q=(uint8_t*)n+bytes;
 for(unsigned i=0;i<count;i++){n->roads[i].command=roads[i].command;n->roads[i].data=q;n->roads[i].size=roads[i].size;memcpy(q,roads[i].data,roads[i].size);q+=roads[i].size;}n->road_count=count;
 n->hud=q;n->text=q+hs;n->hud_size=hs;n->text_size=ts;n->hud_cut=160;n->hud_refresh=view.refresh;n->hud_stable=1;n->hud_proof=*proof;memcpy(q,hud,hs);memcpy(q+hs,text,ts);free(s);*owner=n;return 1;
}

static double nf_motion_owner_mark(void){LARGE_INTEGER now,frequency;QueryPerformanceCounter(&now);QueryPerformanceFrequency(&frequency);return 1000.0*now.QuadPart/frequency.QuadPart;}
/* Validate borrowed inputs, then copy exactly once into the final exclusive owner. */
static int nf_prepared_motion_create_complete_internal(const void*a,size_t an,const void*b,size_t bn,const void*p,size_t pn,const NFRigidPose*c,unsigned cn,double alpha,const NFPreparedRoadAttachment*roads,unsigned count,const void*hud,size_t hs,const void*text,size_t ts,const NFPagePersistenceProof*proof,NFPreparedMotionSubmission**out,NFOwnedRoadSource*shared_a,NFOwnedRoadSource*shared_b,const uint32_t*rows){
 int profile=getenv("NF_TEST_MOTION_OWNER_PROFILE")!=NULL;double begin=profile?nf_motion_owner_mark():0,geometry=0,display=0,pooled=0,allocated=0;
 NFRoadBundle old_view,new_view;if(!out||!proof)return 0;
 if(shared_a||shared_b){if(!shared_a||!shared_b||a!=shared_a->bytes||b!=shared_b->bytes||an!=shared_a->size||bn!=shared_b->size||shared_a->epoch!=shared_b->epoch||shared_a->observer_version!=shared_b->observer_version)return 0;old_view=shared_a->view;new_view=shared_b->view;if(!nf_prepared_motion_geometry_canonical_rows(old_view,new_view,p,pn,c,cn,alpha,rows))return 0;}
 else if(!nf_road_bundle_view(a,an,&old_view)||!nf_road_bundle_view(b,bn,&new_view)||!nf_prepared_motion_geometry_canonical_rows(old_view,new_view,p,pn,c,cn,alpha,rows)){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("motion_owner_validation_failed geometry=1\n");return 0;}
 if(profile)geometry=nf_motion_owner_mark();
 NFPreparedMotionSubmission borrowed={0};borrowed.packet=p;borrowed.packet_size=pn;borrowed.camera_count=cn;size_t extra;NFHudSubmissionView view;
 if(!nf_prepared_motion_roads_valid(&borrowed,roads,count,&extra)){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("motion_owner_validation_failed roads=1\n");return 0;}if(!nf_stable_scene_view_validated(&old_view,hud,hs,text,ts,proof,&view)){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE")){printf("motion_owner_validation_failed display=1\n");printf("motion_display_identity source=%u proof=%u source_end=%u proof_end=%u source_page=%u proof_page=%u refresh=%u\n",old_view.ordered.packet.serial,proof->serial,old_view.ordered.packet.end_refresh,proof->completion_refresh,old_view.ordered.packet.page,proof->page,proof->display_refresh);for(unsigned y=0;y<160&&hs==160*sizeof(NFHudLayerRow);y++){NFHudLayerRow row;memcpy(&row,(const uint8_t*)hud+y*sizeof(row),sizeof(row));unsigned reg=row.registers[0]|((unsigned)row.registers[1]<<8);if(row.refresh!=proof->display_refresh||row.row!=y||(reg&0x8080)||(reg&7)!=4||((reg>>4)&1)!=proof->page){printf("motion_display_row_rejection serial=%u row=%u refresh=%u register=%u expected_page=%u\n",proof->serial,y,row.refresh,reg,proof->page);break;}}}return 0;}
 if(profile)display=nf_motion_owner_mark();
 NFHudRowPool*pool=NULL;size_t stored_hs=hs;if(getenv("NF_TEST_OWNED_HUD_POOL")){pool=nf_hud_pool_create(hud,hs,proof->epoch);if(!pool)return 0;stored_hs=0;}
 if(profile)pooled=nf_motion_owner_mark();
 size_t sizes[]={sizeof(borrowed),cn*sizeof(*c),shared_a?0:an,shared_b?0:bn,pn,extra,stored_hs,ts},total=0;for(unsigned i=0;i<8;i++){if(sizes[i]>SIZE_MAX-total){free(pool);return 0;}total+=sizes[i];}
 NFPreparedMotionSubmission*n=malloc(total);if(!n){free(pool);return 0;}if(profile)allocated=nf_motion_owner_mark();memset(n,0,sizeof(*n));uint8_t*q=(uint8_t*)(n+1);n->alpha=alpha;n->camera_count=cn;n->cameras=(NFRigidPose*)q;memcpy(q,c,cn*sizeof(*c));q+=cn*sizeof(*c);n->older=shared_a?a:q;n->older_size=an;if(!shared_a){memcpy(q,a,an);q+=an;}n->newer=shared_b?b:q;n->newer_size=bn;if(!shared_b){memcpy(q,b,bn);q+=bn;}n->packet=q;n->packet_size=pn;memcpy(q,p,pn);q+=pn;
 for(unsigned i=0;i<count;i++){n->roads[i].command=roads[i].command;n->roads[i].data=q;n->roads[i].size=roads[i].size;memcpy(q,roads[i].data,roads[i].size);q+=roads[i].size;}n->road_count=count;
 n->hud_pool=pool;n->hud=pool?NULL:q;n->text=q+stored_hs;n->hud_size=hs;n->text_size=ts;n->hud_cut=160;n->hud_refresh=view.refresh;n->hud_stable=1;n->hud_proof=*proof;if(!pool)memcpy(q,hud,hs);memcpy(q+stored_hs,text,ts);double copied=profile?nf_motion_owner_mark():0;if(pool)printf("owned_hud_pool full_bytes=%zu stored_bytes=%zu epoch=%llu integrity=%u\n",hs,pool->bytes,(unsigned long long)pool->epoch,pool->layout);if(profile)printf("motion_owner_profile alpha=%.12f geometry_validation=%.6f road_display_validation=%.6f hud_pool_construction=%.6f allocation=%.6f copy=%.6f bytes=%llu header_bytes=%llu camera_bytes=%llu older_bytes=%llu newer_bytes=%llu packet_bytes=%llu road_bytes=%llu hud_bytes=%llu text_bytes=%llu\n",alpha,geometry-begin,display-geometry,pooled-display,allocated-pooled,copied-allocated,(unsigned long long)total,(unsigned long long)sizeof(*n),(unsigned long long)(cn*sizeof(*c)),(unsigned long long)(shared_a?0:an),(unsigned long long)(shared_b?0:bn),(unsigned long long)pn,(unsigned long long)extra,(unsigned long long)stored_hs,(unsigned long long)ts);if(shared_a&&!nf_owned_road_source_retain(shared_a)){free(pool);free(n);return 0;}if(shared_b&&!nf_owned_road_source_retain(shared_b)){nf_owned_road_source_release(shared_a);free(pool);free(n);return 0;}n->shared_older=shared_a;n->shared_newer=shared_b;*out=n;return 1;
}
static int nf_prepared_motion_create_complete(const void*a,size_t an,const void*b,size_t bn,const void*p,size_t pn,const NFRigidPose*c,unsigned cn,double alpha,const NFPreparedRoadAttachment*roads,unsigned count,const void*hud,size_t hs,const void*text,size_t ts,const NFPagePersistenceProof*proof,NFPreparedMotionSubmission**out){return nf_prepared_motion_create_complete_internal(a,an,b,bn,p,pn,c,cn,alpha,roads,count,hud,hs,text,ts,proof,out,NULL,NULL,NULL);}
static int nf_prepared_motion_create_shared(NFOwnedRoadSource*a,NFOwnedRoadSource*b,const void*p,size_t pn,const NFRigidPose*c,unsigned cn,double alpha,const NFPreparedRoadAttachment*roads,unsigned count,const void*hud,size_t hs,const void*text,size_t ts,const NFPagePersistenceProof*proof,NFPreparedMotionSubmission**out){
 if(!a||!b||a==b||a->epoch!=b->epoch||a->observer_version!=b->observer_version)return 0;
 return nf_prepared_motion_create_complete_internal(a->bytes,a->size,b->bytes,b->size,p,pn,c,cn,alpha,roads,count,hud,hs,text,ts,proof,out,a,b,NULL);
}

static int nf_prepared_motion_attach_hud(NFPreparedMotionSubmission**owner,const void*hud,size_t hs,const void*text,size_t ts,unsigned cut){return nf_prepared_motion_attach_display(owner,hud,hs,text,ts,cut,NULL);}
static int nf_prepared_motion_attach_stable_hud(NFPreparedMotionSubmission**owner,const void*hud,size_t hs,const void*text,size_t ts,const NFPagePersistenceProof*proof){return proof&&nf_prepared_motion_attach_display(owner,hud,hs,text,ts,160,proof);}
static int nf_prepared_motion_display_view(const NFPreparedMotionSubmission*s,NFHudSubmissionView*out){if(!s)return 0;if(s->hud_pool){NFRoadBundle a,b;return s->hud_stable&&nf_prepared_motion_source_views(s,&a,&b)&&nf_stable_scene_pool_view_validated(&a,s->hud_pool,s->hud_pool->bytes,s->text,s->text_size,&s->hud_proof,out);}if(s->shared_older||s->shared_newer){NFRoadBundle a,b;if(!nf_prepared_motion_source_views(s,&a,&b))return 0;return s->hud_stable?nf_stable_scene_view_validated(&a,s->hud,s->hud_size,s->text,s->text_size,&s->hud_proof,out):nf_hud_submission_view(&a,&b,s->hud,s->hud_size,s->text,s->text_size,s->hud_cut,out);}if(s->hud_stable)return nf_stable_scene_view(s->older,s->older_size,s->hud,s->hud_size,s->text,s->text_size,&s->hud_proof,out);NFRoadBundle a,b;return nf_road_bundle_view(s->older,s->older_size,&a)&&nf_road_bundle_view(s->newer,s->newer_size,&b)&&nf_hud_submission_view(&a,&b,s->hud,s->hud_size,s->text,s->text_size,s->hud_cut,out);}

/* Explicit full-row export for diagnostic files; failure never publishes partial rows. */
static int nf_prepared_motion_export_hud(const NFPreparedMotionSubmission*s,uint64_t epoch,void*out,size_t bytes){
 NFHudSubmissionView view;if(!s||!out||bytes!=160*sizeof(NFHudLayerRow)||!nf_prepared_motion_display_view(s,&view)||view.epoch!=epoch)return 0;
 if(s->hud_pool)return nf_hud_pool_expand(s->hud_pool,s->hud_pool->bytes,epoch,out,bytes);
 if(!s->hud||s->hud_size!=bytes)return 0;memcpy(out,s->hud,bytes);return 1;
}

#endif









