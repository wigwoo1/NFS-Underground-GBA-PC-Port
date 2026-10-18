#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 if(argc!=3&&argc!=4)return 1;FILE*f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);if(size<64||size>64*1024*1024)return 3;void*data=malloc(size);if(!data||fread(data,1,size,f)!=(size_t)size)return 4;fclose(f);NFRoadBundle source;if(!nf_road_bundle_view(data,size,&source))return 5;
 f=fopen(argv[2],"rb");if(!f)return 6;int valid=fread(preview_display_palette,1,81920,f)==81920&&fgetc(f)==EOF;fclose(f);if(!valid)return 6;
 preview_zero_valid=preview_display_palette_valid=preview_measure_only=preview_keep_context=1;_putenv("NF_PREVIEW_PHASE=0");char*args[]={argv[0],"unused","unused","unused"};int result=render_road_bundle(data,size,args);if(result)return result;
 if(packet_ordered_draws!=source.ordered.asset_count||packet_ordered_geometry!=source.ordered.camera_count||packet_road_matches!=source.count||glGetError()!=GL_NO_ERROR)return 7;
 size_t pixels=3840u*2160u,bytes=pixels*3;void*a=malloc(bytes),*b=malloc(bytes);if(!a||!b)return 8;glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,a);result=render_road_bundle(data,size,args);if(result)return result;glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,b);if(memcmp(a,b,bytes)||glGetError()!=GL_NO_ERROR)return 9;
 if(argc==4){FILE*output=fopen(argv[3],"wb");if(!output)return 10;fprintf(output,"P6\n3840 2160\n255\n");for(unsigned y=0;y<2160;y++)if(fwrite((uint8_t*)a+(2159-y)*3840*3,1,3840*3,output)!=3840*3)return 11;fclose(output);}
 printf("PASS serial=%u geometry=%u operations=%u road_assets=%u repeat_rgb_pixels=%zu\n",source.ordered.packet.serial,packet_ordered_geometry,packet_ordered_draws,packet_road_matches,pixels);preview_shutdown();free(a);free(b);free(data);return 0;
}
