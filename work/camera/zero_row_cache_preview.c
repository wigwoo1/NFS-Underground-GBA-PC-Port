/* Cache lifecycle diagnostic; no ROM or game simulation required. */
#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
static int verify_rows(void){
 uint8_t rgba[640];model_zero_active(0x84c1);
 glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,rgba);
 model_zero_active(0x84c0);
 for(unsigned y=0;y<160;y++)for(unsigned k=0;k<4;k++){
  unsigned c=(preview_zero_colors[y]>>(k*5))&31;
  if(rgba[y*4+k]!=(k==3?255:((c<<3)|(c>>2))))return 0;
 }return glGetError()==GL_NO_ERROR;
}
int main(void){
 int result=preview_context_open();if(result)return result;
 preview_generation++;preview_zero_valid=1;
 uint8_t index=0,skin_pixels[4]={0,0,0,0};
 GLuint skin=preview_texture(1,1,skin_pixels);
 for(unsigned phase=0;phase<4;phase++){
  if(phase==2)preview_generation++;
  if(phase==3)preview_generation+=2;
  for(unsigned y=0;y<160;y++)preview_zero_colors[y]=(uint16_t)((y+phase*997)&32767);
  if(!model_zero_begin(skin,&index)||!verify_rows())return 50;
  model_zero_end(&index);
  unsigned hits=preview_hits,uploads=preview_uploads;
  for(unsigned repeat=0;repeat<12;repeat++){
   if(!model_zero_begin(skin,&index)||!verify_rows())return 51;
   model_zero_end(&index);
  }
  if(preview_hits!=hits||preview_uploads!=uploads)return 52;
 }
 preview_shutdown();puts("PASS row_cache phases=4 repeated_draws=48 exact_texels=8320 same_generation_mutation=1 generation_revalidation=1");return 0;
}

