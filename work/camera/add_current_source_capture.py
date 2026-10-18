from pathlib import Path
p=Path('work/camera/world_trace.h');s=p.read_text()
s=s.replace('static void owned_builder_reset(void){','static uint8_t*owned_current_sources;static size_t owned_current_sources_bytes;\nstatic void owned_builder_reset(void){free(owned_current_sources);owned_current_sources=NULL;owned_current_sources_bytes=0;')
marker='static void owned_graph_live_close(uint64_t epoch,unsigned refresh){'
code='''/* Current closure-time objects for all previously built source identities.
   This is a separately timed diagnostic packet, not a graph-source pose. */
API int nf_owned_current_sources_closed_read(uint64_t epoch,unsigned refresh,void*out,size_t capacity,size_t*bytes){
 if(!bytes||!owned_current_sources||epoch!=nf_native_scene_epoch()||epoch!=owned_graph_closed_epoch||refresh!=owned_graph_closed_refresh)return 0;
 *bytes=owned_current_sources_bytes;if(!out)return 1;if(capacity<*bytes)return 0;memcpy(out,owned_current_sources,*bytes);return 1;
}
static int owned_current_sources_capture(uint64_t epoch,unsigned refresh){
 unsigned addresses[1024],count=0;
 for(unsigned i=0;i<owned_builder_count;i++){unsigned address;memcpy(&address,owned_builder_inputs[i]+12,4);unsigned seen=0;for(unsigned j=0;j<count;j++)if(addresses[j]==address)seen=1;if(!seen)addresses[count++]=address;}
 size_t n=32+count*168;uint8_t*data=malloc(n);if(!data)return 0;
 uint32_t h[6]={0x31534f4e,1,refresh,c->frameCounter(c),count,168};memcpy(data,h,24);memcpy(data+24,&epoch,8);
 for(unsigned i=0;i<count;i++){memcpy(data+32+i*168,&addresses[i],4);if(!validmem(addresses[i],164)||!native_read_owned(addresses[i],data+36+i*168,164)){free(data);return 0;}}
 free(owned_current_sources);owned_current_sources=data;owned_current_sources_bytes=n;return 1;
}
'''
assert marker in s;s=s.replace(marker,code+marker)
needle='unsigned source;memcpy(&source,owned_graph_live_data+4,4);'
assert needle in s
# Capture only when graph closure proceeds; subsequent paired read requires same epoch/refresh.
check='if(!epoch||epoch!=owned_graph_build_epoch||source>refresh||source==owned_graph_closed_source)return;'
assert check in s;s=s.replace(check,check+'if(!owned_current_sources_capture(epoch,refresh))return;')
p.write_text(s)
