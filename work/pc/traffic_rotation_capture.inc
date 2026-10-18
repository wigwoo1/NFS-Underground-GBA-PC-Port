#include "../traffic_rotation_pose.inc"
static struct {unsigned active,phase,camera,object,slot,temp,frame,serial,index;uint64_t epoch;int32_t cm[12],first[12],second[12];} nf_traffic_pending;
static uint64_t nf_traffic_stats[6];
static void nf_traffic_reset(void){memset(&nf_traffic_pending,0,sizeof(nf_traffic_pending));memset(nf_traffic_stats,0,sizeof(nf_traffic_stats));}
static int nf_traffic_rotation_valid(unsigned i,unsigned camera,unsigned object){
 if(!live_scene.rotations[i].traffic)return 1;
 int32_t cm[12],actual[9];
 int ok=live_scene.rotations[i].traffic_object==object&&live_scene.rotations[i].traffic_camera==camera&&live_scene.rotations[i].traffic_epoch==live_scene_epoch&&live_scene.rotations[i].traffic_serial==live_scene.serial&&native_surface_read(NULL,camera,cm,48)&&!memcmp(cm,live_scene.rotations[i].traffic_cm,48)&&native_surface_read(NULL,live_scene.rotations[i].address,actual,36)&&!memcmp(actual,live_scene.rotations[i].traffic_actual,36);
 if(!ok)nf_traffic_stats[4]++;else nf_traffic_stats[2]++;return ok;
}
static int nf_traffic_event(struct ARMCore*cpu,unsigned pc){
 if(pc!=0x08022c24&&pc!=0x08022d38&&pc!=0x08022d44&&pc!=0x08022d48)return 0;
 unsigned*r=(unsigned*)cpu->gprs,frame=c->frameCounter(c);
 if(pc==0x08022c24){
  memset(&nf_traffic_pending,0,sizeof(nf_traffic_pending));nf_traffic_stats[0]++;
  uint8_t index;if(!native_surface_read(NULL,r[0],nf_traffic_pending.cm,48)||!native_surface_read(NULL,r[1]+0x88,&index,1))return 1;
  nf_traffic_pending.camera=r[0];nf_traffic_pending.object=r[1];nf_traffic_pending.slot=r[2];nf_traffic_pending.index=index;nf_traffic_pending.frame=frame;nf_traffic_pending.serial=live_scene.serial;nf_traffic_pending.epoch=live_scene_epoch;nf_traffic_pending.active=1;return 1;
 }
 if(!nf_traffic_pending.active||nf_traffic_pending.epoch!=live_scene_epoch||nf_traffic_pending.serial!=live_scene.serial||nf_traffic_pending.frame!=frame)goto failed;
 if(pc==0x08022d38){
  int32_t camera[12];if(r[2]!=nf_traffic_pending.camera||!native_surface_read(NULL,r[1],nf_traffic_pending.first,36)||!native_surface_read(NULL,r[2],camera,48)||memcmp(camera,nf_traffic_pending.cm,48))goto failed;
  nf_traffic_pending.temp=r[3];nf_traffic_pending.phase=1;return 1;
 }
 if(pc==0x08022d44){
  int32_t expected[12]={0},actual[9];nf_traffic_mul9(nf_traffic_pending.first,nf_traffic_pending.cm,expected);
  if(nf_traffic_pending.phase!=1||r[1]!=nf_traffic_pending.temp||r[3]!=nf_traffic_pending.slot||!native_surface_read(NULL,r[1],actual,36)||memcmp(expected,actual,36)||!native_surface_read(NULL,r[2],nf_traffic_pending.second,36))goto failed;
  nf_traffic_pending.phase=2;return 1;
 }
 if(!nf_traffic_pending.phase){nf_traffic_pending.active=0;nf_traffic_stats[5]++;return 1;}
 if(nf_traffic_pending.phase==2){
  int32_t actual[12]={0},camera[12],rotation[12];uint8_t index;
  if(r[8]!=nf_traffic_pending.slot||!native_surface_read(NULL,nf_traffic_pending.slot,actual,36)||!native_surface_read(NULL,nf_traffic_pending.camera,camera,48)||memcmp(camera,nf_traffic_pending.cm,48)||!native_surface_read(NULL,nf_traffic_pending.object+0x88,&index,1)||index!=nf_traffic_pending.index||!nf_traffic_rotation_pose(camera,nf_traffic_pending.first,nf_traffic_pending.second,actual,rotation))goto failed;
  unsigned i=0;for(;i<16;i++)if(live_scene.rotations[i].address==nf_traffic_pending.slot)break;if(i==16)i=live_scene.slot++%16;
  live_scene.rotations[i].address=nf_traffic_pending.slot;live_scene.rotations[i].frame=frame;memcpy(live_scene.rotations[i].matrix,rotation,48);
  live_scene.rotations[i].traffic=1;live_scene.rotations[i].traffic_object=nf_traffic_pending.object;live_scene.rotations[i].traffic_camera=nf_traffic_pending.camera;live_scene.rotations[i].traffic_epoch=live_scene_epoch;live_scene.rotations[i].traffic_serial=live_scene.serial;memcpy(live_scene.rotations[i].traffic_cm,camera,48);memcpy(live_scene.rotations[i].traffic_actual,actual,36);
  nf_traffic_pending.active=0;nf_traffic_stats[1]++;return 1;
 }
failed:nf_traffic_pending.active=0;nf_traffic_stats[3]++;return 1;
}
