
/* Staged-only compact owned layer representation; canonical PC file unchanged. */
size_t nf_android_layer_pack(const NFLayerSnapshot*s,void*out,size_t capacity){
 if(!s||s->count!=160||!s->pages||s->pages>MAXPAGES)return 0;
 uint32_t refresh;memcpy(&refresh,s->headers[0],4);
 for(unsigned y=0;y<160;y++){uint32_t identity[2];memcpy(identity,s->headers[y],8);if(identity[0]!=refresh||identity[1]!=y)return 0;for(unsigned part=0;part<PARTS;part++)if(s->refs[y][part]>=s->pages)return 0;}
 size_t bytes=32+sizeof(s->headers)+sizeof(s->refs)+(size_t)s->pages*PAGE;
 if(!out)return bytes;if(capacity<bytes)return 0;
 uint32_t header[8]={0x31504c4e,1,(uint32_t)bytes,160,s->pages,PARTS,PAGE,refresh};
 uint8_t*dst=out;memcpy(dst,header,32);dst+=32;memcpy(dst,s->headers,sizeof(s->headers));dst+=sizeof(s->headers);memcpy(dst,s->refs,sizeof(s->refs));dst+=sizeof(s->refs);memcpy(dst,s->data,(size_t)s->pages*PAGE);return bytes;
}
