#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define adjustment reference_adjustment
#define endpoint reference_endpoint
#define nf_road_clip_continuous nf_road_clip_reference
#include "road_clip_continuous_before_bounds_fastpath.c"
#undef nf_road_clip_continuous
#undef endpoint
#undef adjustment
#define adjustment candidate_adjustment
#define endpoint candidate_endpoint
#define nf_road_clip_continuous nf_road_clip_fast_candidate
#include "road_clip_continuous.c"
#undef nf_road_clip_continuous
#undef endpoint
#undef adjustment
static uint64_t state=0x5eed20261011ULL;
static uint32_t next_u32(void){state=state*6364136223846793005ULL+1442695040888963407ULL;return (uint32_t)(state>>32);}
static double unit(void){return (double)(next_u32()&0x00ffffffu)/16777216.0;}
static int compare(const double*input,unsigned count,double left,double right,const uint32_t*table,unsigned capacity,unsigned *checked){
 double a[128*6]={0},b[128*6]={0};unsigned na=777,nb=777;
 int ra=nf_road_clip_reference(input,count,left,right,table,a,capacity,&na);
 int rb=nf_road_clip_fast_candidate(input,count,left,right,table,b,capacity,&nb);
 (*checked)++;
 if(ra!=rb||na!=nb||(ra&&memcmp(a,b,na*6*sizeof(double)))){
  fprintf(stderr,"Mismatch trial %u count %u bounds %.17g %.17g cap %u results %d/%d counts %u/%u\n",*checked,count,left,right,capacity,ra,rb,na,nb);return 0;
 }
 return 1;
}
int main(void){
 uint32_t table[32768];FILE*f=fopen("work/camera/road-correction-reciprocal.bin","rb");if(!f)return 2;
 if(fread(table,sizeof(table),1,f)!=1||fgetc(f)!=EOF){fclose(f);return 3;}fclose(f);
 unsigned checked=0;double input[64*6];
 for(unsigned trial=0;trial<25000;trial++){
  unsigned n=next_u32()%65,mode=trial%5,capacity=next_u32()%129;double left=-10+50*unit(),right=left+.01+100*unit();
  for(unsigned i=0;i<n;i++){
   double x;
   if(mode==0)x=-30+160*unit();
   else if(mode==1)x=-10+120*unit();
   else if(mode==2){static const double edge[]={-.5,0,1,99.999,100,100.001};x=edge[next_u32()%6];}
   else if(mode==3)x=-32760+65520*unit();
   else x=-1000000+2000000*unit();
   input[i*6]=x;
   for(unsigned k=1;k<6;k++)input[i*6+k]=-100000+200000*unit();
  }
  if(!compare(input,n,left,right,table,capacity,&checked))return 4;
 }
 for(unsigned i=0;i<64;i++){
  input[i*6]=(i&1)?125.25:-25.5;input[i*6+1]=i*.125;input[i*6+2]=-1.5+i*.25;
  input[i*6+3]=10000-i*3.125;input[i*6+4]=.375-i*.03125;input[i*6+5]=-500+i*7.75;
 }
 if(!compare(input,64,.25,100.75,table,128,&checked))return 5;
 for(unsigned i=0;i<64;i++){input[i*6]=i*1.25;input[i*6+1]=i*.5;input[i*6+2]=2;input[i*6+3]=i*.125;input[i*6+4]=1;input[i*6+5]=-2;}
 if(!compare(input,64,-100,100,table,128,&checked))return 6;
 for(unsigned i=0;i<64;i++)input[i*6]=-10-i;
 if(!compare(input,64,0,100,table,128,&checked))return 7;
 printf("PASS_ROAD_CLIP_BOUNDS_FASTPATH_EXACT_PARITY %u cases\n",checked);return 0;
}

