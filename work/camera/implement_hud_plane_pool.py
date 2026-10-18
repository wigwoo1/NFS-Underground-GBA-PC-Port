from pathlib import Path
p=Path('work/camera/hud_row_pool.h');s=p.read_text().replace('uint32_t refresh,count;','uint32_t refresh,count,layout;',1)
start=s.index('static int nf_hud_pool_valid(');end=s.index('static NFHudRowPool*nf_hud_pool_create(',start)
s=s[:start]+'''static int nf_hud_pool_extent(const NFHudRowPool*p,size_t bytes){
 if(!p||bytes<sizeof(*p)||p->bytes!=bytes)return 0;
 if(p->layout==1)return p->count&&p->count<=160&&bytes==sizeof(*p)+(size_t)p->count*NF_HUD_POOL_PAYLOAD;
 if(p->layout!=2||(p->count>>24))return 0;
 unsigned a=p->count&255,b=p->count>>8&255,c=p->count>>16&255;
 return a&&a<=160&&b&&b<=160&&c&&c<=160&&bytes==sizeof(*p)+(size_t)a*32768+(size_t)(b+c)*1024;
}
static int nf_hud_pool_index_valid(const NFHudRowPool*p,unsigned row){
 unsigned i=p->indices[row];if(p->layout==1)return i<p->count;
 return !(i>>24)&&(i&255)<(p->count&255)&&(i>>8&255)<(p->count>>8&255)&&(i>>16&255)<(p->count>>16&255);
}
static int nf_hud_pool_valid(const NFHudRowPool*p,size_t bytes,uint64_t epoch){
 if(!nf_hud_pool_extent(p,bytes)||!epoch||p->epoch!=epoch)return 0;
 for(unsigned i=0;i<160;i++)if(p->headers[i].row!=i||p->headers[i].refresh!=p->refresh||!nf_hud_pool_index_valid(p,i))return 0;
 return p->hash==nf_hud_pool_hash(p);
}
static NFHudRowPool*nf_hud_pool_create_planes(const void*data,size_t bytes,uint64_t epoch){
 if(!data||!epoch||bytes!=160*sizeof(NFHudLayerRow))return NULL;
 const uint8_t*b=data;unsigned unique[3][160],counts[3]={0},indices[160]={0};size_t offsets[3]={offsetof(NFHudLayerRow,obj_vram),offsetof(NFHudLayerRow,palette),offsetof(NFHudLayerRow,oam)},lengths[3]={32768,1024,1024};uint32_t refresh;memcpy(&refresh,b,4);
 for(unsigned row=0;row<160;row++){NFHardwareLayerHeader h;memcpy(&h,b+row*sizeof(NFHudLayerRow),sizeof(h));if(h.row!=row||h.refresh!=refresh)return NULL;
  for(unsigned plane=0;plane<3;plane++){unsigned j=counts[plane];const uint8_t*current=b+row*sizeof(NFHudLayerRow)+offsets[plane];
   if(row){unsigned previous=indices[row-1]>>(plane*8)&255;if(!memcmp(current,b+unique[plane][previous]*sizeof(NFHudLayerRow)+offsets[plane],lengths[plane]))j=previous;}
   if(j==counts[plane]){for(j=0;j<counts[plane];j++)if(!memcmp(current,b+unique[plane][j]*sizeof(NFHudLayerRow)+offsets[plane],lengths[plane]))break;}
   if(j==counts[plane])unique[plane][counts[plane]++]=row;
   indices[row]|=j<<(plane*8);
  }
 }
 size_t size=sizeof(NFHudRowPool);for(unsigned i=0;i<3;i++)size+=(size_t)counts[i]*lengths[i];NFHudRowPool*p=calloc(1,size);if(!p)return NULL;p->epoch=epoch;p->refresh=refresh;p->layout=2;p->count=counts[0]|counts[1]<<8|counts[2]<<16;p->bytes=size;
 for(unsigned i=0;i<160;i++){memcpy(p->headers+i,b+i*sizeof(NFHudLayerRow),sizeof(p->headers[i]));p->indices[i]=indices[i];}
 size_t at=0;for(unsigned plane=0;plane<3;plane++)for(unsigned j=0;j<counts[plane];j++){memcpy(p->payload+at,b+unique[plane][j]*sizeof(NFHudLayerRow)+offsets[plane],lengths[plane]);at+=lengths[plane];}
 p->hash=nf_hud_pool_hash(p);return p;
}
'''+s[end:]
s=s.replace('static NFHudRowPool*nf_hud_pool_create(const void*data,size_t bytes,uint64_t epoch){','static NFHudRowPool*nf_hud_pool_create(const void*data,size_t bytes,uint64_t epoch){\n if(getenv("NF_TEST_HUD_POOL_PLANES"))return nf_hud_pool_create_planes(data,bytes,epoch);',1)
s=s.replace('p->refresh=refresh;p->count=count;','p->refresh=refresh;p->layout=1;p->count=count;',1)
start=s.index(' if(!p||!out||row>=160||p->epoch!=epoch');end=s.index('\n}',start)
s=s[:start]+''' if(!out||row>=160||!nf_hud_pool_extent(p,bytes)||p->epoch!=epoch||!epoch||!nf_hud_pool_index_valid(p,row))return 0;
 NFHudLayerRow value;memcpy(&value,p->headers+row,sizeof(NFHardwareLayerHeader));
 if(p->layout==1)memcpy(value.obj_vram,p->payload+(size_t)p->indices[row]*NF_HUD_POOL_PAYLOAD,NF_HUD_POOL_PAYLOAD);
 else {unsigned index=p->indices[row],a=p->count&255,b=p->count>>8&255;memcpy(value.obj_vram,p->payload+(size_t)(index&255)*32768,32768);memcpy(value.palette,p->payload+(size_t)a*32768+(size_t)(index>>8&255)*1024,1024);memcpy(value.oam,p->payload+(size_t)a*32768+(size_t)b*1024+(size_t)(index>>16&255)*1024,1024);}
 *out=value;return 1;'''+s[end:];p.write_text(s)
p=Path('work/camera/audit_threaded_racing_motion.py');s=p.read_text().replace("for flag in ['NF_TEST_CLOCK_POLL_TRACE'","for flag in ['NF_TEST_HUD_POOL_PLANES','NF_TEST_CLOCK_POLL_TRACE'").replace('int(a)+672','int(a)+688');p.write_text(s)
p=Path('work/camera/analyze_queued_hud_pool.py');p.write_text(p.read_text().replace('int(a)+672','int(a)+688'))
