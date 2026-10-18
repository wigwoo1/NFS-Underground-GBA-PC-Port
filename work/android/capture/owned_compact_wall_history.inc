/* Compact source events, shared immutable assets; no finished pixel storage. */
static FILE*owned_compact_wall_file;static uint64_t owned_compact_wall_epoch;static unsigned owned_compact_wall_assets,owned_compact_wall_events,owned_compact_wall_failed;static size_t owned_compact_wall_bytes;
static struct{unsigned category,address,bytes;uint64_t hash;uint8_t*data;} owned_compact_wall_asset[1024];
static uint64_t owned_compact_wall_hash(const uint8_t*p,size_t n){uint64_t h=1469598103934665603ull;for(size_t i=0;i<n;i++){h^=p[i];h*=1099511628211ull;}return h;}
static unsigned owned_compact_wall_asset_id(unsigned category,unsigned address,const uint8_t*data,unsigned bytes){
 uint64_t hash=owned_compact_wall_hash(data,bytes);for(unsigned i=0;i<owned_compact_wall_assets;i++)if(owned_compact_wall_asset[i].category==category&&owned_compact_wall_asset[i].address==address&&owned_compact_wall_asset[i].bytes==bytes&&owned_compact_wall_asset[i].hash==hash&&!memcmp(data,owned_compact_wall_asset[i].data,bytes))return i+1;
 if(owned_compact_wall_assets>=1024||owned_compact_wall_bytes+bytes>32u*1024u*1024u)return 0;unsigned i=owned_compact_wall_assets;uint8_t*copy=malloc(bytes);if(!copy)return 0;memcpy(copy,data,bytes);
 uint64_t h[8]={1,64u+bytes,i+1,category,address,bytes,0,0};if(fwrite(h,1,64,owned_compact_wall_file)!=64||fwrite(data,1,bytes,owned_compact_wall_file)!=bytes){free(copy);return 0;}
 owned_compact_wall_asset[i].category=category;owned_compact_wall_asset[i].address=address;owned_compact_wall_asset[i].bytes=bytes;owned_compact_wall_asset[i].hash=hash;owned_compact_wall_asset[i].data=copy;owned_compact_wall_assets++;owned_compact_wall_bytes+=bytes;return i+1;
}
NF_TEXT_HOST_EXPORT void nf_owned_compact_wall_close(uint32_t out[4]){
 unsigned size=0;if(owned_compact_wall_file){long end=ftell(owned_compact_wall_file);if(end<64||end>64*1024*1024)owned_compact_wall_failed=1;else size=(unsigned)end;uint64_t h[8]={0x3148574e,1,size,owned_compact_wall_epoch,owned_compact_wall_assets,owned_compact_wall_events,0,0};if(fseek(owned_compact_wall_file,0,SEEK_SET)||fwrite(h,1,64,owned_compact_wall_file)!=64)owned_compact_wall_failed=1;if(fclose(owned_compact_wall_file))owned_compact_wall_failed=1;owned_compact_wall_file=NULL;}
 if(out){out[0]=owned_compact_wall_assets;out[1]=owned_compact_wall_events;out[2]=owned_compact_wall_failed;out[3]=size;}for(unsigned i=0;i<owned_compact_wall_assets;i++)free(owned_compact_wall_asset[i].data);memset(owned_compact_wall_asset,0,sizeof(owned_compact_wall_asset));owned_compact_wall_assets=0;owned_compact_wall_bytes=0;
}
NF_TEXT_HOST_EXPORT int nf_owned_compact_wall_open(const char*path){nf_owned_compact_wall_close(NULL);owned_compact_wall_events=owned_compact_wall_failed=0;owned_compact_wall_epoch=nf_native_scene_epoch();if(!c||!path||!native_original_wall_spans)return 0;owned_compact_wall_file=fopen(path,"wb");if(!owned_compact_wall_file)return 0;uint64_t h[8]={0x3148574e,1,64,owned_compact_wall_epoch,0,0,0,0};if(fwrite(h,1,64,owned_compact_wall_file)!=64){owned_compact_wall_failed=1;return 0;}return 1;}
static int nf_owned_compact_wall_event(const NFSceneEvent*e,unsigned ordinal,unsigned refresh){
 if(!owned_compact_wall_file)return 1;if(owned_compact_wall_failed||!native_original_wall_spans||owned_compact_wall_epoch!=nf_native_scene_epoch()||e->count!=1||e->shift>1||e->texture_size!=65536+(e->shift?4081:0)||owned_compact_wall_events>=65536)return 0;
 unsigned texture=owned_compact_wall_asset_id(1,e->texture_address,e->texture,65536),shade=0;if(!texture)return 0;
 if(e->shift){int16_t offset;memcpy(&offset,(const uint8_t*)e->commands+42,2);uint32_t address=e->commands[5]+(int32_t)offset;shade=owned_compact_wall_asset_id(2,address,e->texture+65536,4081);if(!shade)return 0;}
 uint64_t h[12]={2,176,ordinal,refresh,texture,shade,e->texture_address,1,e->shift,0,0,0};if(fwrite(h,1,96,owned_compact_wall_file)!=96||fwrite(e->commands,1,80,owned_compact_wall_file)!=80){owned_compact_wall_failed=1;return 0;}owned_compact_wall_events++;return 1;
}
