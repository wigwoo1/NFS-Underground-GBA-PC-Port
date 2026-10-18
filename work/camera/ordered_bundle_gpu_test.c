#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 if(argc!=2&&argc!=3)return 1;FILE*f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);
 if(size<64||size>64*1024*1024)return 3;void*data=malloc(size);if(!data||fread(data,1,size,f)!=(size_t)size)return 4;fclose(f);
 NFOrderedBundle bundle;NFRoadBundle roads;int road_mode=nf_bundle_word(data)==0x4252464e;
 if(road_mode){if(!nf_road_bundle_view(data,size,&roads))return 5;bundle=roads.ordered;}else if(!nf_ordered_bundle_view(data,size,&bundle))return 5;
 preview_zero_valid=preview_display_palette_valid=1;preview_measure_only=1;preview_keep_context=1;
 for(unsigned y=0;y<160;y++)for(unsigned i=0;i<256;i++)preview_display_palette[y][i]=(i*131+y*997)&32767;
 if(argc==3){FILE*palette=fopen(argv[2],"rb");if(!palette)return 14;int ok=fread(preview_display_palette,1,81920,palette)==81920&&fgetc(palette)==EOF;fclose(palette);if(!ok)return 14;printf("palette_source=owned_original_scanlines\n");}
 _putenv("NF_PREVIEW_PHASE=0");char*args[]={argv[0],"unused","unused","unused"};int result=(road_mode?render_road_bundle(data,size,args):render_ordered_bundle(data,size,args));
 if(road_mode){printf("road_material_matches=%u expected=%u\n",packet_road_matches,roads.count);if(packet_road_matches!=roads.count)return 12;}
 GLenum error=glGetError();printf("gl_error=%u expected_assets=%u expected_geometry=%u\n",error,bundle.asset_count,bundle.camera_count);if(!result&&(packet_ordered_draws!=bundle.asset_count||packet_ordered_geometry!=bundle.camera_count||error!=GL_NO_ERROR))result=6;
 if(!result){
  size_t bytes=3840u*2160u*3;uint8_t*a=malloc(bytes),*b=malloc(bytes);if(!a||!b)return 7;
  glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,a);
  if(road_mode){unsigned expected[2][3]={{107,107,107},{109,119,109}},which=bundle.packet.serial==22?0:1,edge_checks=0;
   /* Independent original final-pass indices, whole4K cells at x238/239.
      x237 remains continuous interior and has separate projection semantics. */
   for(unsigned x=238;x<=239;x++){unsigned color=preview_display_palette[143][expected[which][x-237]];
    for(unsigned yy=(unsigned)ceil(143*13.5-.5);yy<(unsigned)ceil(144*13.5-.5);yy++)for(unsigned xx=300+(unsigned)ceil(x*13.5-.5);xx<300+(unsigned)ceil((x+1)*13.5-.5);xx++){
     uint8_t*pixel=a+((2159-yy)*3840+xx)*3;if(pixel[0]!=(color&31)*255/31||pixel[1]!=((color>>5)&31)*255/31||pixel[2]!=((color>>10)&31)*255/31){printf("edge_color_mismatch=%u,%u expected_index=%u\n",xx,yy,expected[which][x-237]);return 13;}edge_checks++;
    }}printf("exact_edge_gpu_pixels=%u\n",edge_checks);
  }
  unsigned checked=0,fill_checked=0,protected_bottom=144;const uint8_t*bounds;double bounds_alpha;if(!nf_scene_packet_bounds(&bundle.packet,&bounds_alpha,&bounds))return 11;unsigned world=nf_bundle_word(bundle.packet.section[1].data+4);for(unsigned i=0;i<world;i++){uint16_t clip[4];memcpy(clip,bounds+i*8,8);if(clip[3]>protected_bottom)protected_bottom=clip[3];}
  for(unsigned y=0;y<2160;y++)for(unsigned x=300;x<3540;x++){
   unsigned row=(unsigned)floor((2160-y-.5)/13.5);const uint8_t*pixel=a+(y*3840+x)*3;int match=0;
   for(unsigned index=0;index<256&&!match;index++){
    unsigned color=preview_display_palette[row][index];match=pixel[0]==(color&31)*255/31&&pixel[1]==((color>>5)&31)*255/31&&pixel[2]==((color>>10)&31)*255/31;
   }
   if(!match){printf("nonpalette_pixel=%u,%u\n",x,y);return 8;}checked++;
   if(row<16||row>=protected_bottom){unsigned index=row<16?169:193,color=preview_display_palette[row][index];
    if(pixel[0]!=(color&31)*255/31||pixel[1]!=((color>>5)&31)*255/31||pixel[2]!=((color>>10)&31)*255/31){printf("fill_mismatch=%u,%u rgb=%u,%u,%u expected_index=%u row=%u\n",x,y,pixel[0],pixel[1],pixel[2],index,row);return 9;}fill_checked++;}
  }
  result=(road_mode?render_road_bundle(data,size,args):render_ordered_bundle(data,size,args));if(result)return result;
  glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,b);if(memcmp(a,b,bytes)||glGetError()!=GL_NO_ERROR)return 10;
  printf("PASS palette_pixels=%u final_fill_pixels=%u protected_bottom=%u repeat_rgb_exact=1\n",checked,fill_checked,protected_bottom);free(a);free(b);
 }
 printf("ordered_bundle_gpu result=%d operations=%u geometry=%u\n",result,packet_ordered_draws,packet_ordered_geometry);
 preview_shutdown();free(data);return result;
}
