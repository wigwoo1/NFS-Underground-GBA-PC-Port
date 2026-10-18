#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 if(argc!=3)return 1;
 NFSnapshotStore*s=nf_snapshot_create(32*1024*1024);NFScenePacket a,b;
 if(!s||!enqueue_file(s,argv[1],&a)||!enqueue_file(s,argv[2],&b))return 2;
 preview_keep_context=1;preview_measure_only=1;_putenv("NF_PREVIEW_PHASE=0");
 char*args[]={argv[0],"unused","unused","unused"};
 if(render_packet_at(s,(a.end_refresh+b.end_refresh)/2.,args))return 3;
 RoadPreview*r=roads;memset(r,0,sizeof(*r));r->count=4;r->lit=1;r->intensity[1]=15;
 for(unsigned level=0;level<16;level++){
  uint8_t pixel[4]={(uint8_t)(level*16+8),32,(uint8_t)(248-level*16),255};
  r->variants[level]=preview_texture(1,1,pixel);if(!r->variants[level])return 4;
 }r->texture=r->variants[0];
 NFRigidPose poses[2]={{{0,0,0},{0,0,0,1}},{{0,0,0},{0,0,0,1}}};double projection[3]={120,80,120};
 double ends[]={120.8,121.4,122.99,123.01,124,128};
 FILE*f=fopen("work/camera/wall-pixel-sweep.csv","wb");if(!f)return 5;
 fprintf(f,"case,right,mode,pixel_x,red,green,blue\n");
 unsigned checked=0,mismatch=0;uint8_t line[3840*3];
 for(unsigned test=0;test<sizeof(ends)/sizeof(*ends);test++){
  double left=120.2,right=ends[test],z=1000;
  r->vertices[0]=(NFPoint3){(left-120)*z/120,-100,z};
  r->vertices[1]=(NFPoint3){(right-120)*z/120,-100,z};
  r->vertices[2]=(NFPoint3){(right-120)*z/120,100,z};
  r->vertices[3]=(NFPoint3){(left-120)*z/120,100,z};
  int shades[3240];int mode=wall_shades(r,r->vertices,projection,shades);
  glDisable(GL_SCISSOR_TEST);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);
  draw_road_range(poses,0,projection,0,1);glFinish();
  glReadPixels(0,1080,3840,1,GL_RGB,GL_UNSIGNED_BYTE,line);if(glGetError()!=GL_NO_ERROR)return 6;
  for(unsigned x=0;x<3840;x++){
   double p=(x-300.+.5)*240/3240;
   if(mode==2&&p>left+1e-6&&p<right-1e-6){
    /* Equal depth makes the independent reference a simple linear ramp. */
    int level=(int)floor((p-left)/(right-left)*15+1e-10);
    mismatch+=line[x*3]!=level*16+8||line[x*3+1]!=32||line[x*3+2]!=248-level*16;checked++;
   }
   if(x>=1918&&x<2040)fprintf(f,"%u,%.6f,%d,%u,%u,%u,%u\n",test,right,mode,x,line[x*3],line[x*3+1],line[x*3+2]);
  }
 }
 fclose(f);printf("native_narrow_checked_pixels=%u mismatches=%u boundary_sweep_cases=6\n",checked,mismatch);
 const double depths[][2]={{128,512},{32,128},{128,32},{32,48},{63.99,128},{64.01,128}};
 unsigned depth_checked=0,depth_mismatch=0,background_checked=0;
 FILE*depth_log=fopen("work/camera/wall-depth-sweep.csv","wb");if(!depth_log)return 8;
 fprintf(depth_log,"case,pixel_x,expected_level,red,green,blue\n");
 for(unsigned test=0;test<sizeof(depths)/sizeof(*depths);test++){
  double z0=depths[test][0],z1=depths[test][1];
  r->vertices[0]=(NFPoint3){-10,-100,z0};r->vertices[1]=(NFPoint3){10,-100,z1};
  r->vertices[2]=(NFPoint3){10,100,z1};r->vertices[3]=(NFPoint3){-10,100,z0};
  glDisable(GL_SCISSOR_TEST);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);
  draw_road_range(poses,0,projection,0,1);glFinish();
  glReadPixels(0,1080,3840,1,GL_RGB,GL_UNSIGNED_BYTE,line);if(glGetError()!=GL_NO_ERROR)return 9;
  for(unsigned px=300;px<3540;px++){
   /* Independent ray/segment intersection in camera space: x(t)/z(t)=ray.
      Compare against ORIGINAL endpoints; do not reuse the clipping/shade code. */
   double ray=(((px-300.+.5)*240/3240)-120)/120;
   double t=(ray*z0+10)/(20-ray*(z1-z0)),depth=z0+t*(z1-z0);
   int covered=t>0&&t<1&&depth>=64;
   int level=covered?(int)floor(15*t+1e-10):-1;
   if(covered){depth_checked++;depth_mismatch+=line[px*3]!=level*16+8||line[px*3+1]!=32||line[px*3+2]!=248-level*16;}
   else{background_checked++;depth_mismatch+=line[px*3]!=0||line[px*3+1]!=0||line[px*3+2]!=0;}
   fprintf(depth_log,"%u,%u,%d,%u,%u,%u\n",test,px,level,line[px*3],line[px*3+1],line[px*3+2]);
  }
 }
 fclose(depth_log);
 printf("depth_and_near_plane_cases=6 covered_pixels=%u background_pixels=%u mismatches=%u\n",depth_checked,background_checked,depth_mismatch);
 preview_shutdown();nf_snapshot_destroy(s);return mismatch||depth_mismatch||!checked||!depth_checked?7:0;
}
