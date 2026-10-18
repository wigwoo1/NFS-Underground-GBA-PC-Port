#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(void){
 int error=preview_context_open();if(error)return error;preview_generation++;preview_zero_valid=1;
 uint8_t states[51];states[0]=0;states[1]=states[2]=2;
 for(unsigned level=0;level<16;level++){states[3+level*3]=0;states[4+level*3]=level%2?1:2;states[5+level*3]=2;}
 size_t bytes=8+20+16*12+131072;uint8_t*data=calloc(1,bytes);if(!data)return 1;
 uint32_t header[7]={0x314c464e,1,1,0,15,3,1};memcpy(data,header,28);
 for(unsigned level=0;level<16;level++)for(unsigned x=0;x<3;x++){uint8_t*p=data+28+level*12+x*4;p[0]=(uint8_t)(level*13);p[1]=(uint8_t)x;p[3]=255;}
 road_count=1;roads[0].count=4;roads[0].width=3;roads[0].height=1;preview_wall_states[0]=states;preview_wall_planes[0]=17;preview_memory[4]=(PreviewMemory){data,bytes};
 if(!load_wall_lighting("memory"))return 2;
 for(unsigned level=0;level<16;level++){
  uint8_t pixels[12];glBindTexture(GL_TEXTURE_2D,roads[0].variants[level]);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
  for(unsigned x=0;x<3;x++){uint8_t expected[4]={(uint8_t)(level*13),(uint8_t)x,0,states[3+level*3+x]==0?0:states[3+level*3+x]==1?128:255};if(memcmp(pixels+x*4,expected,4))return 3;}
 }
 preview_wall_planes[0]=1;if(load_wall_lighting("memory"))return 4;
 packet_extra_release();if(preview_wall_states[0]||preview_wall_planes[0])return 5;
 free(data);memset(preview_memory,0,sizeof(preview_memory));puts("PASS wall_lighting_classifications levels=16 texels=48 mismatched_planes_rejected=1 borrowed_state_cleared=1");return 0;
}
